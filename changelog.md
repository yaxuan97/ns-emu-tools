# Change Log

## 0.2.1
 - 更新 Edge 的检测机制，在无法检测到 Edge 时将尝试使用默认浏览器启动
 - 添加命令行启动参数，支持选择启动的浏览器 (chrome, edge, user default)
   - 例如强制使用默认浏览器启动 `NsEmuTools.exe -m "user default"`
 - 添加 常见问题 页面
 - 设置中添加更多的 GitHub 下载源选项
 - 更换游戏数据源
 - 修复 Yuzu 路径有特殊字符时无法检测版本的问题
 - 设置中添加选项，允许保留下载的文件 (#4)

## 0.2.0
 - 新增 Yuzu 金手指管理功能
 - 调整 aria2p 连接参数以修复某些情况下 aria2 接口调用失败的问题
 - 修复含有特殊字符路径时命令行无法执行的问题
 - 在修改模拟器目录时展示警告信息

## 0.1.9
 - aria2 禁用 ipv6
 - 新增网络设置相关选项
 - 添加 requests-cache 用于本地缓存 api 结果

## 0.1.8
 - 修复 windowed 打包方式无法正常启动 Edge 浏览器的问题

## 0.1.7
 - 基于 Vuetify 构建的新 UI
 - 添加 msvc 的代理源
 - 修复 Ryujinx 切换分支后由于版本相同导致无法开始下载的问题
 - 调整浏览器默认使用顺序: Chrome > Edge > User Default
