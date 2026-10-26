# 发布到 AeroL1n 的独立公开仓库

## 当前与目标

目标：新建公开仓库 `AeroL1n/mov-sticker-to-transparent-gif`。

本项目仓库地址为 [AeroL1n/mov-sticker-to-transparent-gif](https://github.com/AeroL1n/mov-sticker-to-transparent-gif)，首次内容通过用户授权后提交。下方保留网页上传和 CLI 发布流程，方便理解或另建副本；不要对已经存在的同名仓库重复执行新建命令。后续更新应先拉取远程内容，检查改动后再提交。GitHub Release 需另行发布，上传仓库不等于已建立 Release。

不要把 GitHub 密码、Token、SSH 私钥或浏览器 Cookie 发送到聊天、放入 README 或写进远程 URL。授权应使用 GitHub 正规登录流程。

## 方式 A：网页上传，无需命令行

1. 登录 GitHub，确认当前账户为 `AeroL1n`，选择 **New repository**。
2. 名称输入 `mov-sticker-to-transparent-gif`，可填简介：
   > MOV 表情包转透明白描边三尺寸 GIF 的 Claude Skill，支持中文文件名、安全追加和批次打包。
3. 选择 **Public**。不要添加空白 README、`.gitignore` 或自动许可证，避免和本地内容冲突；许可证需要你另行决定。
4. 创建后选择 **uploading an existing file** / **Add file → Upload files**。
5. 如拿到的是仓库准备包，先在本地解压；打开其中的 `mov-sticker-to-transparent-gif/`，上传**里面的内容**，不要只上传最外层 ZIP 或再嵌套一层同名文件夹。
6. 确保仓库根目录能直接看到 `README.md`、`SKILL.md`、`scripts/`、`docs/`、`dist/` 等。隐藏的 `.gitignore` 也应上传；Finder 可用 `Command + Shift + .` 显示隐藏文件。
7. 填写提交说明，例如 `Add sticker GIF skill v2.3.0 and Chinese documentation`，确认提交。
8. 打开主页检查 README 图、文档相对链接、`dist/` 技能包下载是否正常。网页上传到 GitHub 不等于自动安装到 Claude。

当前真实 MOV/GIF 示例尚未提供；可以先发布源码与明确标注的说明图，或等待补齐真实素材后一起发布。不要把说明图说成已验证的真实效果。

## 方式 B：Git + GitHub CLI

在自己电脑安装 Git 和 GitHub CLI 后，用正规浏览器流程授权；这里没有在当前会话中执行推送。

```bash
gh auth login
gh auth status
```

确认登录账户为 AeroL1n，再进入**已经检查过且准备公开的仓库目录**：

```bash
cd "/实际路径/mov-sticker-to-transparent-gif"
git init -b main
git status --short
# 检查无凭证、私人源片、测试临时文件后再继续
git add .
git diff --cached --stat
git commit -m "Add sticker GIF skill v2.3.0 with Chinese documentation"
gh repo create AeroL1n/mov-sticker-to-transparent-gif \
  --public --source=. --remote=origin --push
```

若 Git 首次提交要求配置姓名/邮箱，请按自己的隐私偏好设置；可使用 GitHub 提供的 noreply 邮箱，不在此自动写入假身份。如目标同名仓库已存在，不要强推或删除；先拉取并检查远程内容，调整流程。

## 可选：发布 v2.3.0 Release

仓库创建并推送成功后，可在 GitHub **Releases → Draft a new release** 中选择/创建标签 `v2.3.0`，将 `dist/表情包转GIF_v2.3.skill.zip` 上传为附件，说明目录规则及安装方法。

也可以在已认证、仓库内容已推送的情况下执行：

```bash
gh release create v2.3.0 "dist/表情包转GIF_v2.3.skill.zip" \
  --repo AeroL1n/mov-sticker-to-transparent-gif \
  --title "v2.3.0 · 尺寸+gif 目录规则" \
  --notes "三尺寸目录统一为120gif/220gif/330gif；文件名只用表情名；保留去噪点和安全追加规则。"
```

请在实际成功后再把 Release 链接写进主页，不能预先写成“已发布”。

## 发布检查清单

- [ ] 仓库由正确账户创建，公开范围已确认；
- [ ] README 在根目录，三张说明图能显示，链接可点击；
- [ ] `SKILL.md` 与转换脚本版本均为 2.3.0；
- [ ] 专用技能 ZIP 可下载/导入，没有混入整个仓库或私人媒体；
- [ ] 如加入真实素材，已确认公开权利并提供来源说明；
- [ ] 没有凭证、个人路径、`.DS_Store`、虚拟环境或调试中间文件；
- [ ] 许可证由作者明确选择；未选择时不宣称是某种开源许可；
- [ ] 网页上传/推送实际完成后，记录真实仓库链接再对外分享。
