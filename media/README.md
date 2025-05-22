# 视频处理工具集

这是一个功能强大的视频处理工具集，支持视频拼接、缩放效果、音频处理等多种功能。

## 主要功能

- 视频拼接（支持简单拼接和高级拼接）
- 自动缩放效果
- 音频音量调整
- 视频格式统一
- GPU 加速支持
- 批量处理
- 智能补充视频时长

## 安装依赖

```bash
pip install ffmpeg-python pathlib psutil tqdm
```

确保系统已安装 FFmpeg：

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# 请从 https://ffmpeg.org/download.html 下载并配置环境变量
```

## 命令行参数说明

### 基础参数

- `--input`, `-i`：输入视频文件夹路径（必需）

  ```bash
  python video_contact_zoom.py -i /path/to/videos
  ```

- `--output`, `-o`：输出视频文件路径（可选，默认为输入文件夹下的 output_with_zoom.mp4）
  ```bash
  python video_contact_zoom.py -i /path/to/videos -o /path/to/output.mp4
  ```

### 视频参数

- `--width`：输出视频宽度（默认：720）
- `--height`：输出视频高度（默认：1280）
  ```bash
  python video_contact_zoom.py -i /path/to/videos --width 1080 --height 1920
  ```

### 缩放效果参数

- `--min-interval`：缩放效果最小间隔，单位秒（默认：60）
- `--max-interval`：缩放效果最大间隔，单位秒（默认：120）
- `--zoom-scale`：缩放比例（默认：2）
- `--zoom-duration`：缩放持续时间，单位秒（默认：10）
- `--no-preset-zoom`：禁用预设缩放点
  ```bash
  python video_contact_zoom.py -i /path/to/videos --min-interval 30 --max-interval 60 --zoom-scale 3 --zoom-duration 5
  ```

### 音频参数

- `--audio-volume`：最终音频音量比例（默认：0.15）
- `--audio-quality`：音频质量模式 [fast/normal/high]（默认：fast）
  ```bash
  python video_contact_zoom.py -i /path/to/videos --audio-volume 0.2 --audio-quality high
  ```

### 性能参数

- `--batch-size`：每批次处理的视频数量（默认：5）
- `--max-workers`：并行处理的最大工作线程数，0 表示自动（默认：0）
- `--video-preset`：视频编码预设 [ultrafast/veryfast/fast/medium]（默认：ultrafast）
  ```bash
  python video_contact_zoom.py -i /path/to/videos --batch-size 10 --max-workers 4 --video-preset veryfast
  ```

### GPU 加速

- `--use-gpu`：使用 GPU 加速（需要 NVIDIA 显卡和 NVENC 支持）
- `--gpu-preset`：NVENC 预设质量 [p1-p7]（默认：p2）
  ```bash
  python video_contact_zoom.py -i /path/to/videos --use-gpu --gpu-preset p3
  ```

### 拼接模式

- `--simple-concat`：使用简单拼接模式（直接拼接，不重编码）
- `--force-encode`：简单拼接模式下，强制统一编码格式

  ```bash
  # 简单拼接模式
  python video_contact_zoom.py -i /path/to/videos --simple-concat

  # 强制编码格式统一
  python video_contact_zoom.py -i /path/to/videos --simple-concat --force-encode
  ```

### 文件处理参数

- `--max-clips`：最大处理片段数，0 表示不限制（默认：0）
- `--sample-strategy`：文件超过最大处理数时的采样策略 [random/first/duration/all]（默认：all）
- `--no-skip-existing`：不跳过已存在的编码文件
  ```bash
  python video_contact_zoom.py -i /path/to/videos --max-clips 20 --sample-strategy duration
  ```

## 使用示例

1. 基本拼接（默认参数）：

```bash
python video_contact_zoom.py -i /path/to/videos
```

2. 高质量输出：

```bash
python video_contact_zoom.py -i /path/to/videos \
    --video-preset medium \
    --audio-quality high \
    --width 1920 \
    --height 1080
```

3. 快速处理（低质量）：

```bash
python video_contact_zoom.py -i /path/to/videos \
    --video-preset ultrafast \
    --audio-quality fast \
    --simple-concat
```

4. GPU 加速处理：

```bash
python video_contact_zoom.py -i /path/to/videos \
    --use-gpu \
    --gpu-preset p2 \
    --max-workers 4
```

5. 自定义缩放效果：

```bash
python video_contact_zoom.py -i /path/to/videos \
    --min-interval 45 \
    --max-interval 90 \
    --zoom-scale 2.5 \
    --zoom-duration 8
```

## 注意事项

1. 内存使用：

    - 处理大量视频时，建议设置适当的 `--batch-size` 和 `--max-workers`
    - 对于大量文件，建议使用 `--max-clips` 限制处理数量

2. GPU 加速：

    - 仅支持 NVIDIA 显卡（Windows/Linux）或 VideoToolbox（macOS）
    - 确保已安装相应的硬件编码器驱动

3. 性能优化：

    - 使用 `--simple-concat` 可以显著提高处理速度
    - `--video-preset` 设置会影响处理速度和质量

4. 存储空间：
    - 确保有足够的磁盘空间用于临时文件
    - 建议输出目录有原始视频总大小 2-3 倍的可用空间

## 常见问题

1. 如果遇到内存不足：

   ```bash
   # 减小批次大小和工作线程数
   python video_contact_zoom.py -i /path/to/videos --batch-size 3 --max-workers 2
   ```

2. 如果处理速度太慢：

   ```bash
   # 使用简单拼接模式和快速预设
   python video_contact_zoom.py -i /path/to/videos --simple-concat --video-preset ultrafast
   ```

3. 如果视频格式不一致：
   ```bash
   # 强制编码格式统一
   python video_contact_zoom.py -i /path/to/videos --force-encode
   ```

## 版本历史

- v1.0.0：初始版本

    - 基本视频拼接功能
    - 缩放效果支持
    - 音频处理

- v1.1.0：性能优化
    - 添加 GPU 加速支持
    - 添加简单拼接模式
    - 优化内存使用

## 许可证

本项目采用 MIT 许可证。
