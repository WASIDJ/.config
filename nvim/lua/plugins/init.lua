return {
  {
    "stevearc/conform.nvim",
    event = "BufWritePre",
    opts = require "configs.conform",
  },

  -- These are some examples, uncomment them if you want to see them work!
  {
    "neovim/nvim-lspconfig",
    config = function()
      require "configs.lspconfig"
    end,
  },

  {
    "hrsh7th/nvim-cmp",
    opts = function()
      return require "configs.cmp"
    end,
  },

  {
    "folke/sidekick.nvim",
    opts = {
      nes = { enabled = false },
      cli = {
        tools = {
          codex = {
            cmd = { "codex", "--sandbox", "workspace-write" },
          },
        },
      },
    },
    keys = {
      {
        "<leader>aa",
        function()
          require("sidekick.cli").toggle { name = "codex", focus = true }
        end,
        desc = "AI: toggle Codex",
      },
      {
        "<leader>at",
        function()
          require("sidekick.cli").send { name = "codex", msg = "{this}", focus = true }
        end,
        mode = { "n", "x" },
        desc = "AI: send this to Codex",
      },
    },
  },

  -- test new blink
  -- { import = "nvchad.blink.lazyspec" },

  -- {
  -- 	"nvim-treesitter/nvim-treesitter",
  -- 	opts = {
  -- 		ensure_installed = {
  -- 			"vim", "lua", "vimdoc",
  --      "html", "css"
  -- 		},
  -- 	},
  -- },

  {
    "epwalsh/obsidian.nvim",
    version = "*",
    ft = "markdown",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "hrsh7th/nvim-cmp",
      "nvim-telescope/telescope.nvim",
    },
    opts = {
      workspaces = {
        {
          name = "note",
          path = "/Users/ryou/Documents/NOTE",
        },
      },

      notes_subdir = "00-Inbox",
      new_notes_location = "notes_subdir",
      preferred_link_style = "wiki",
      disable_frontmatter = true,

      daily_notes = {
        folder = "Daily",
        date_format = "%Y-%m-%d",
        alias_format = "%Y-%m-%d",
        default_tags = {},
        template = nil,
      },

      completion = {
        nvim_cmp = true,
        min_chars = 2,
      },

      templates = {
        folder = "Templates",
        date_format = "%Y-%m-%d",
        time_format = "%H:%M",
      },

      picker = {
        name = "telescope.nvim",
      },

      ui = {
        enable = false,
      },

      attachments = {
        img_folder = "assets/imgs",
      },
    },
  },

  {
    "nvim-treesitter/nvim-treesitter",
    opts = function(_, opts)
      opts.ensure_installed = opts.ensure_installed or {}

      local parsers = {
        "markdown",
        "markdown_inline",
        "go",
        "gomod",
        "gowork",
        "gosum",
      }

      for _, parser in ipairs(parsers) do
        if not vim.tbl_contains(opts.ensure_installed, parser) then
          table.insert(opts.ensure_installed, parser)
        end
      end
    end,
  },

  {
    "ray-x/lsp_signature.nvim",
    event = "VeryLazy",
    opts = {
      bind = true,
      handler_opts = {
        border = "rounded",
      },
      hint_enable = false,
    },
    config = function(_, opts)
      require("lsp_signature").setup(opts)
    end,
  },

  {
    "MeanderingProgrammer/render-markdown.nvim",
    ft = { "markdown", "Avante" },
    dependencies = {
      "nvim-treesitter/nvim-treesitter",
      "nvim-mini/mini.nvim",
    },
    opts = {
      render_modes = true,
      anti_conceal = {
        enabled = false,
      },
      heading = {
        enabled = true,
        sign = false,
        icons = { "󰎤 ", "󰎧 ", "󰎪 ", "󰎭 ", "󰎱 ", "󰎳 " },
      },
      code = {
        sign = false,
        width = "block",
        right_pad = 1,
      },
      bullet = {
        enabled = true,
      },
      checkbox = {
        enabled = true,
      },
    },
  },
}
