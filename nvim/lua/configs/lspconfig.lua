require("nvchad.configs.lspconfig").defaults()

vim.lsp.config("gopls", {
  settings = {
    gopls = {
      gofumpt = true,
      completeUnimported = true,
      usePlaceholders = true,
      staticcheck = true,
      analyses = {
        nilness = true,
        unusedparams = true,
        unusedwrite = true,
        useany = true,
      },
      hints = {
        assignVariableTypes = true,
        compositeLiteralFields = true,
        parameterNames = true,
        rangeVariableTypes = true,
      },
      directoryFilters = { "-.git", "-.vscode", "-.idea", "-node_modules" },
      codelenses = {
        generate = true,
        test = true,
        tidy = true,
        vendor = true,
        upgrade_dependency = true,
      },
    },
  },
})

local servers = { "html", "cssls", "gopls", "denols" }
vim.lsp.enable(servers)
