-- ~/.config/yazi/init.lua
-- 插件初始化（插件通过 ya pkg add 安装，这里统一 setup）

-- git 状态显示为 linemode
require("git"):setup {
    order = 1500,
}

-- full-border: 给 yazi 加圆角边框，配 catppuccin-mocha 更协调
require("full-border"):setup {
    set = "rounded",
}

-- eza-preview: 目录预览默认用树状视图
require("eza-preview"):setup {
    default_tree   = true,
    level          = 3,
    icons          = true,
    follow_symlinks = true,
    dereference    = false,
    all            = true,
    ignore_glob    = { ".git", "node_modules", ".DS_Store" },
}
