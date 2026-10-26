# 真实素材示例

此目录现包含「太强了、得意、比心、加油」四组真实 MOV/GIF，由用户为技能展示提供。

- MOV：480×480、30fps，只含视频的公开副本；编辑器元数据与音轨已移除，视频流不重新编码，解码画面逐帧与上传原片一致。
- GIF：120×120、220×220、330×330，透明背景、白描边、无限循环，均由 v2.3 从对应上传 MOV 生成。四份330pxGIF与用户提供的成品逐字节一致。
- `source-preview.gif`：220px、约15fps的黑底预览，保留全部输入时长，仅用于README显示，并非MOV本体。
- `source-cover.png`：MOV第15帧封面。
- `preview-on-backgrounds.png`：成品第15帧分别放在白/灰/深底上，仅为静态边缘检查。
- `processing-report.json`：本次转换参数、去尾数量和各尺寸输出校验值。
- `ATTRIBUTION.md`：素材来源、改动和权利声明，不额外授予再分发或商用权利。

## 文件入口

| 表情 | MOV（视频公开副本） | 120gif | 220gif | 330gif | 封面 / 检查 |
| --- | --- | --- | --- | --- | --- |
| 太强了 | [MOV](strong/太强了.mov?raw=true) | [120px](strong/120gif/太强了.gif) | [220px](strong/220gif/太强了.gif) | [330px](strong/330gif/太强了.gif) | [封面](strong/source-cover.png) · [边缘](strong/preview-on-backgrounds.png) |
| 得意 | [MOV](cool/得意.mov?raw=true) | [120px](cool/120gif/得意.gif) | [220px](cool/220gif/得意.gif) | [330px](cool/330gif/得意.gif) | [封面](cool/source-cover.png) · [边缘](cool/preview-on-backgrounds.png) |
| 比心 | [MOV](heart/比心.mov?raw=true) | [120px](heart/120gif/比心.gif) | [220px](heart/220gif/比心.gif) | [330px](heart/330gif/比心.gif) | [封面](heart/source-cover.png) · [边缘](heart/preview-on-backgrounds.png) |
| 加油 | [MOV](cheer/加油.mov?raw=true) | [120px](cheer/120gif/加油.gif) | [220px](cheer/220gif/加油.gif) | [330px](cheer/330gif/加油.gif) | [封面](cheer/source-cover.png) · [边缘](cheer/preview-on-backgrounds.png) |

## 校验与范围

完整校验记录见 [MEDIA_MANIFEST.json](MEDIA_MANIFEST.json)。所有12个GIF经脚本重新解码验证尺寸、循环、时序、透明与白边；仅「太强了」裁尾32帧，其余不裁尾。黑底四例不代表脚本支持所有复杂背景。

原始MOV含AAC音轨和编辑器标签；公开副本不含音轨/编辑器标签。GIF本身不支持声音，README仅比较画面，不作音频转换展示。
