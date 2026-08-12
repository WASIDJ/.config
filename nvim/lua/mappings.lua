require "nvchad.mappings"

-- add yours here

local map = vim.keymap.set

map("n", ";", ":", { desc = "CMD enter command mode" })
map("i", "jk", "<ESC>")

map("n", "<leader>on", "<cmd>ObsidianNew<cr>", { desc = "Obsidian new note" })
map("n", "<leader>ot", "<cmd>ObsidianToday<cr>", { desc = "Obsidian today" })
map("n", "<leader>oy", "<cmd>ObsidianYesterday<cr>", { desc = "Obsidian yesterday" })
map("n", "<leader>of", "<cmd>ObsidianQuickSwitch<cr>", { desc = "Obsidian quick switch" })
map("n", "<leader>os", "<cmd>ObsidianSearch<cr>", { desc = "Obsidian search" })
map("n", "<leader>ol", "<cmd>ObsidianLinks<cr>", { desc = "Obsidian links" })
map("n", "<leader>ob", "<cmd>ObsidianBacklinks<cr>", { desc = "Obsidian backlinks" })
map("n", "<leader>oo", "<cmd>ObsidianOpen<cr>", { desc = "Obsidian open in app" })

-- map({ "n", "i", "v" }, "<C-s>", "<cmd> w <cr>")

map("n", "<leader>rr", function()
  require("nvchad.term").runner {
    id = "goRunner",
    pos = "sp",
    size = 0.3,
    cmd = function()
      return "go run " .. vim.fn.shellescape(vim.fn.expand "%:p")
    end,
  }
end, { desc = "go run current file" })

map("n", "<leader>rb", function()
  require("nvchad.term").runner {
    id = "goBuilder",
    pos = "sp",
    size = 0.3,
    cmd = "go build ./...",
  }
end, { desc = "go build" })

map("n", "<leader>rt", function()
  require("nvchad.term").runner {
    id = "goTester",
    pos = "sp",
    size = 0.3,
    cmd = "go test ./...",
  }
end, { desc = "go test" })
