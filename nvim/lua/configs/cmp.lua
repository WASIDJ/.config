local cmp = require "cmp"
local luasnip = require "luasnip"

local options = require "nvchad.configs.cmp"

local function has_words_before()
  local line, col = unpack(vim.api.nvim_win_get_cursor(0))
  if col == 0 then
    return false
  end

  local text = vim.api.nvim_buf_get_lines(0, line - 1, line, true)[1]
  return text:sub(col, col):match "%s" == nil
end

options.completion = {
  completeopt = "menu,menuone,noselect",
}

options.preselect = cmp.PreselectMode.None

options.mapping = vim.tbl_extend("force", options.mapping or {}, {
  ["<CR>"] = cmp.mapping.confirm {
    behavior = cmp.ConfirmBehavior.Insert,
    select = false,
  },
  ["<Tab>"] = cmp.mapping(function(fallback)
    if cmp.visible() then
      cmp.select_next_item { behavior = cmp.SelectBehavior.Select }
    elseif luasnip.expand_or_jumpable() then
      luasnip.expand_or_jump()
    elseif has_words_before() then
      cmp.complete()
    else
      fallback()
    end
  end, { "i", "s" }),
  ["<S-Tab>"] = cmp.mapping(function(fallback)
    if cmp.visible() then
      cmp.select_prev_item { behavior = cmp.SelectBehavior.Select }
    elseif luasnip.jumpable(-1) then
      luasnip.jump(-1)
    else
      fallback()
    end
  end, { "i", "s" }),
})

local source_labels = {
  nvim_lsp = "LSP",
  luasnip = "Snippet",
  buffer = "Buffer",
  nvim_lua = "Lua",
  async_path = "Path",
  obsidian = "Obsidian",
  obsidian_new = "Obsidian new",
  obsidian_tags = "Obsidian tag",
}

local original_format = options.formatting and options.formatting.format
if original_format then
  options.formatting.format = function(entry, item)
    item = original_format(entry, item)
    local source = source_labels[entry.source.name] or entry.source.name
    item.menu = string.format("%s  [%s]", item.menu or "", source)
    return item
  end
end

return options
