require "nvchad.options"

vim.env.PATH = table.concat({
  vim.env.HOME .. "/.local/bin",
  vim.env.HOME .. "/go/bin",
  vim.env.PATH,
}, ":")

vim.opt.completeopt = { "menu", "menuone", "noselect" }
vim.opt.pumheight = 12

-- local o = vim.o
-- o.cursorlineopt ='both' -- to enable cursorline!
