#!/usr/bin/env lua

local HOME = os.getenv("HOME") or "/home/ryou"
local CACHE_HOME = os.getenv("XDG_CACHE_HOME") or (HOME .. "/.cache")
local CACHE_DIR = CACHE_HOME .. "/tmux"
local CACHE_FILE = CACHE_DIR .. "/codex-usage-status"
local LOCK_DIR = CACHE_DIR .. "/codex-usage-status.lock"
local LOCK_FILE = LOCK_DIR .. "/created_at"
local AUTH_FILE = HOME .. "/.codex/auth.json"
local USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"
local PROXY_URL = os.getenv("CODEX_USAGE_PROXY") or "http://127.0.0.1:7890"
local TTL_SECONDS = 180
local LOCK_TTL_SECONDS = 60
local CURL_TIMEOUT_SECONDS = 8

local function shell_quote(value)
  return "'" .. tostring(value):gsub("'", [['"'"']]) .. "'"
end

local function ensure_cache_dir()
  os.execute("mkdir -p " .. shell_quote(CACHE_DIR) .. " >/dev/null 2>&1")
end

local function read_file(path)
  local file = io.open(path, "r")
  if not file then
    return nil
  end
  local content = file:read("*a")
  file:close()
  return content
end

local function write_file(path, content)
  local file = io.open(path, "w")
  if not file then
    return false
  end
  file:write(content)
  file:close()
  return true
end

local function now()
  return os.time()
end

local function parse_cache(content)
  local cache = {}
  if not content then
    return cache
  end

  for key, value in content:gmatch("([%w_]+)=([^\n]*)") do
    cache[key] = value
  end

  cache.updated_at = tonumber(cache.updated_at) or 0
  cache.percent = tonumber(cache.percent)
  cache.reset_in = tonumber(cache.reset_in)
  cache.primary_percent = tonumber(cache.primary_percent)
  cache.primary_reset_at = tonumber(cache.primary_reset_at)
  cache.secondary_percent = tonumber(cache.secondary_percent)
  cache.secondary_reset_at = tonumber(cache.secondary_reset_at)
  cache.reset_count = tonumber(cache.reset_count)
  return cache
end

local function write_cache(primary_percent, primary_reset_at, secondary_percent, secondary_reset_at, reset_count, error_message)
  ensure_cache_dir()
  local payload = table.concat({
    "updated_at=" .. now(),
    "primary_percent=" .. (primary_percent or ""),
    "primary_reset_at=" .. (primary_reset_at or ""),
    "secondary_percent=" .. (secondary_percent or ""),
    "secondary_reset_at=" .. (secondary_reset_at or ""),
    "reset_count=" .. (reset_count or ""),
    "error=" .. (error_message or ""),
    "",
  }, "\n")
  write_file(CACHE_FILE, payload)
end

local function write_error_cache(error_message)
  local cache = parse_cache(read_file(CACHE_FILE))
  write_cache(
    cache.primary_percent,
    cache.primary_reset_at,
    cache.secondary_percent,
    cache.secondary_reset_at,
    cache.reset_count,
    error_message
  )
end

local function clamp(value, min_value, max_value)
  if value < min_value then
    return min_value
  end
  if value > max_value then
    return max_value
  end
  return value
end

local function format_reset_at(timestamp)
  if not timestamp then
    return "--:--"
  end

  timestamp = math.floor(timestamp)
  if os.date("%Y-%m-%d", timestamp) == os.date("%Y-%m-%d") then
    return os.date("%H:%M", timestamp)
  end
  return os.date("%m-%d %H:%M", timestamp)
end

local function limit_label(name, percent, reset_at)
  if percent then
    percent = clamp(math.floor(percent + 0.5), 0, 100)
  end
  local pct_label = percent and string.format("%d%%", percent) or "--%"
  return string.format("%s %s@%s", name, pct_label, format_reset_at(reset_at))
end

local function render()
  local cache = parse_cache(read_file(CACHE_FILE))
  local age = now() - (cache.updated_at or 0)

  if age > TTL_SECONDS then
    local script = arg[0]
    os.execute("/opt/homebrew/bin/lua " .. shell_quote(script) .. " update >/dev/null 2>&1 &")
  end

  local primary_percent = cache.primary_percent
  local primary_reset_at = cache.primary_reset_at
  local secondary_percent = cache.secondary_percent
  local secondary_reset_at = cache.secondary_reset_at

  if not primary_percent and cache.percent then
    primary_percent = cache.percent
    if cache.reset_in then
      primary_reset_at = cache.updated_at + cache.reset_in
    end
  end

  if not primary_percent and not secondary_percent and cache.error and cache.error ~= "" then
    io.write("err")
    return
  end

  -- Codex previously exposed a five-hour primary window plus a weekly
  -- secondary window. Newer accounts expose the weekly limit as the only
  -- primary window, so prefer secondary and otherwise fall back to primary.
  local weekly_percent = secondary_percent or primary_percent
  local weekly_reset_at = secondary_reset_at or primary_reset_at
  io.write(limit_label("W", weekly_percent, weekly_reset_at))
  io.write(string.format("  R %d", cache.reset_count or 0))
end

local function acquire_lock()
  ensure_cache_dir()
  local ok = os.execute("mkdir " .. shell_quote(LOCK_DIR) .. " >/dev/null 2>&1")
  if ok == true or ok == 0 then
    write_file(LOCK_FILE, tostring(now()))
    return true
  end

  local created_at = tonumber(read_file(LOCK_FILE) or "")
  if not created_at or now() - created_at > LOCK_TTL_SECONDS then
    os.remove(LOCK_FILE)
    os.execute("rmdir " .. shell_quote(LOCK_DIR) .. " >/dev/null 2>&1")
    ok = os.execute("mkdir " .. shell_quote(LOCK_DIR) .. " >/dev/null 2>&1")
    if ok == true or ok == 0 then
      write_file(LOCK_FILE, tostring(now()))
      return true
    end
  end

  return false
end

local function release_lock()
  os.remove(LOCK_FILE)
  os.execute("rmdir " .. shell_quote(LOCK_DIR) .. " >/dev/null 2>&1")
end

local function json_string_field(content, name)
  return content:match('"' .. name .. '"%s*:%s*"([^"]+)"')
end

local function json_number_field(content, name)
  local value = content:match('"' .. name .. '"%s*:%s*([%d%.]+)')
  return value and tonumber(value) or nil
end

local function parse_window(body, window)
  local window_data = body:match('"' .. window .. '"%s*:%s*{(.-)}')
  if not window_data then
    return nil, nil, "missing " .. window
  end

  local used_percent = json_number_field(window_data, "used_percent")
  local reset_at = json_number_field(window_data, "reset_at")
  local reset_in = json_number_field(window_data, "reset_after_seconds")
  if not used_percent then
    return nil, nil, "missing " .. window .. ".used_percent"
  end
  if not reset_at and reset_in then
    reset_at = now() + reset_in
  end
  if not reset_at then
    return nil, nil, "missing " .. window .. ".reset_at"
  end

  return clamp(100 - math.floor(used_percent + 0.5), 0, 100), math.floor(reset_at), nil
end

local function curl_config_path()
  return CACHE_DIR .. "/codex-usage-curl.conf"
end

local function curl_escape(value)
  return tostring(value):gsub("\\", "\\\\"):gsub('"', '\\"')
end

local function fetch_usage(access_token, account_id)
  local config_path = curl_config_path()
  local config = table.concat({
    'url = "' .. curl_escape(USAGE_URL) .. '"',
    "silent",
    "show-error",
    "fail",
    "location",
    "max-time = " .. CURL_TIMEOUT_SECONDS,
    'proxy = "' .. curl_escape(PROXY_URL) .. '"',
    'header = "Authorization: Bearer ' .. curl_escape(access_token) .. '"',
    'header = "ChatGPT-Account-Id: ' .. curl_escape(account_id) .. '"',
    'header = "Accept: application/json"',
    "",
  }, "\n")

  if not write_file(config_path, config) then
    return nil, "failed to write curl config"
  end
  os.execute("chmod 600 " .. shell_quote(config_path) .. " >/dev/null 2>&1")

  local handle = io.popen("curl --config " .. shell_quote(config_path) .. " 2>&1")
  if not handle then
    os.remove(config_path)
    return nil, "failed to start curl"
  end

  local body = handle:read("*a")
  local ok = handle:close()
  os.remove(config_path)

  if not ok or not body or body == "" then
    local detail = body and body:gsub("[\r\n]+", " "):sub(1, 120) or ""
    if detail ~= "" then
      return nil, "usage request failed: " .. detail
    end
    return nil, "usage request failed"
  end
  return body, nil
end

local function update()
  if not acquire_lock() then
    return
  end

  local ok, err = pcall(function()
    local auth = read_file(AUTH_FILE)
    if not auth then
      write_error_cache("missing auth")
      return
    end

    local access_token = json_string_field(auth, "access_token")
    local account_id = json_string_field(auth, "account_id")
    if not access_token or not account_id then
      write_error_cache("missing token")
      return
    end

    local body, fetch_error = fetch_usage(access_token, account_id)
    if not body then
      write_error_cache(fetch_error)
      return
    end

    local reset_data = body:match('"rate_limit_reset_credits"%s*:%s*{(.-)}')
    local reset_count = reset_data and json_number_field(reset_data, "available_count") or 0

    local primary_percent, primary_reset_at, primary_error = parse_window(body, "primary_window")
    if primary_error then
      write_error_cache(primary_error)
      return
    end

    local secondary_percent, secondary_reset_at, secondary_error = parse_window(body, "secondary_window")
    if secondary_error then
      write_cache(primary_percent, primary_reset_at, nil, nil, reset_count, secondary_error)
      return
    end

    write_cache(primary_percent, primary_reset_at, secondary_percent, secondary_reset_at, reset_count, nil)
  end)

  if not ok then
    write_error_cache(tostring(err))
  end
  release_lock()
end

if arg[1] == "update" then
  update()
else
  render()
end
