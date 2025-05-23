# 视频处理工具集

这是一个功能强大的视频处理工具集，支持视频拼接、缩放效果、随机旋转、镜像和音频处理等多种功能。

## 主要功能

- 视频拼接（支持简单拼接和高级拼接）
- 自动缩放效果
- 随机旋转视频（可配置角度和比例）
- 随机镜像视频
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
  python video_contact.py -i /path/to/videos
  ```

- `--output`, `-o`：输出视频文件路径（可选，默认为输入文件夹下的 output_with_zoom.mp4）
  ```bash
  python video_contact.py -i /path/to/videos -o /path/to/output.mp4
  ```

### 视频参数

- `--width`：输出视频宽度（默认：720）
- `--height`：输出视频高度（默认：1280）
  ```bash
  python video_contact.py -i /path/to/videos --width 1080 --height 1920
  ```

### 缩放效果参数

- `--min-interval`：缩放效果最小间隔，单位秒（默认：60）
- `--max-interval`：缩放效果最大间隔，单位秒（默认：120）
- `--zoom-scale`：缩放比例（默认：2）
- `--zoom-duration`：缩放持续时间，单位秒（默认：10）
- `--no-preset-zoom`：禁用预设缩放点
  ```bash
  python video_contact.py -i /path/to/videos --min-interval 30 --max-interval 60 --zoom-scale 3 --zoom-duration 5
  ```

### 随机镜像和旋转参数

- `--random-mirror`：随机对部分素材做左右镜像
- `--mirror-ratio`：镜像素材比例，范围0~1（默认：0.33）
- `--random-rotate`：随机对部分素材进行旋转
- `--rotate-angle`：旋转角度，单位度（默认：15）
- `--rotate-ratio`：旋转素材比例，范围0~1（默认：0.25）
- `--rotate-scale`：旋转素材放大比例，值越大黑边越少（默认：1.5）
  ```bash
  python video_contact.py -i /path/to/videos --random-mirror --mirror-ratio 0.5 --random-rotate --rotate-angle 20
  ```

### 音频参数

- `--audio-volume`：最终音频音量比例（默认：0.15）
- `--audio-quality`：音频质量模式 [fast/normal/high]（默认：fast）
- `--preserve-audio-channels`：保留原始音频声道数，不强制转换为双声道
- `--handle-complex-audio`：处理复杂音频流，解决可能的音频同步问题
- `--audio-normalize`：对音频进行动态范围压缩和音量均衡化处理
  ```bash
  python video_contact.py -i /path/to/videos --audio-volume 0.2 --audio-quality high --audio-normalize
  ```

### 视频补充模式

- `--append-mode`：视频补充模式 [random/sequential/alternating]（默认：alternating）
  ```bash
  python video_contact.py -i /path/to/videos --append-mode random
  ```

### 性能参数

- `--batch-size`：每批次处理的视频数量（默认：5）
- `--max-workers`：并行处理的最大工作线程数，0 表示自动（默认：0）
- `--video-preset`：视频编码预设 [ultrafast/veryfast/fast/medium]（默认：ultrafast）
  ```bash
  python video_contact.py -i /path/to/videos --batch-size 10 --max-workers 4 --video-preset veryfast
  ```

### GPU 加速

- `--use-gpu`：使用 GPU 加速（需要 NVIDIA 显卡和 NVENC 支持）
- `--gpu-preset`：NVENC 预设质量 [p1-p7]（默认：p2）
- `--encoder`：指定编码器 [auto/h264_nvenc/h264_videotoolbox/h264_qsv/h264_amf/libx264]（默认：auto）
  ```bash
  python video_contact.py -i /path/to/videos --use-gpu --gpu-preset p3 --encoder h264_nvenc
  ```

### 拼接模式

- `--simple-concat`：使用简单拼接模式（直接拼接，不重编码）
- `--force-encode`：简单拼接模式下，强制统一编码格式

  ```bash
  # 简单拼接模式
  python video_contact.py -i /path/to/videos --simple-concat

  # 强制编码格式统一
  python video_contact.py -i /path/to/videos --simple-concat --force-encode
  ```

### 文件处理参数

- `--max-clips`：最大处理片段数，0 表示不限制（默认：0）
- `--sample-strategy`：文件超过最大处理数时的采样策略 [random/first/duration/all]（默认：all）
- `--no-skip-existing`：不跳过已存在的编码文件
- `--min-duration`：最小总时长，单位秒（默认：300）
  ```bash
  python video_contact.py -i /path/to/videos --max-clips 20 --sample-strategy duration --min-duration 600
  ```

## 使用示例

1. 基本拼接（默认参数）：

```bash
python video_contact.py -i /path/to/videos
```

2. 高质量输出：

```bash
python video_contact.py -i /path/to/videos \
    --video-preset medium \
    --audio-quality high \
    --width 1920 \
    --height 1080
```

3. 带随机效果的处理：

```bash
python video_contact.py -i /path/to/videos \
    --random-mirror --mirror-ratio 0.3 \
    --random-rotate --rotate-angle 15 --rotate-scale 1.8
```

4. GPU 加速处理：

```bash
python video_contact.py -i /path/to/videos \
    --use-gpu \
    --gpu-preset p2 \
    --max-workers 4
```

5. 静音视频处理：

```bash
python video_contact.py -i /path/to/videos \
    --audio-volume 0 \
    --min-duration 1200
```

## 常用命令组合

1. 通用高质量视频：
```bash
python video_contact.py -i /path/to/videos --video-preset veryfast --audio-quality normal --audio-volume 0.15 --min-duration 1200
```

2. 无声视频，带随机效果：
```bash
python video_contact.py -i /path/to/videos --use-gpu --audio-volume 0 --min-duration 1200 --max-workers 0 --video-preset veryfast --random-mirror --random-rotate --append-mode random
```

3. 极速处理：
```bash
python video_contact.py -i /path/to/videos --simple-concat --video-preset ultrafast --audio-quality fast --max-workers 0
```

## 注意事项

1. 内存使用：

    - 处理大量视频时，建议设置适当的 `--batch-size` 和 `--max-workers`
    - 对于大量文件，建议使用 `--max-clips` 限制处理数量

2. GPU 加速：

    - 支持NVIDIA(h264_nvenc)、Mac(h264_videotoolbox)、Intel(h264_qsv)和AMD(h264_amf)硬件编码器
    - 确保已安装相应的硬件编码器驱动

3. 性能优化：

    - 使用 `--simple-concat` 可以显著提高处理速度
    - `--video-preset` 设置会影响处理速度和质量

4. 旋转和镜像：
    - 旋转视频会自动添加适当放大以避免黑边
    - 同一个素材不会同时被应用镜像和旋转效果
    - 可以通过 `--rotate-scale` 参数调整旋转时的放大比例

5. 存储空间：
    - 确保有足够的磁盘空间用于临时文件
    - 建议输出目录有原始视频总大小 2-3 倍的可用空间

## 常见问题

1. 如果遇到内存不足：

   ```bash
   # 减小批次大小和工作线程数
   python video_contact.py -i /path/to/videos --batch-size 3 --max-workers 2
   ```

2. 如果处理速度太慢：

   ```bash
   # 使用简单拼接模式和快速预设
   python video_contact.py -i /path/to/videos --simple-concat --video-preset ultrafast
   ```

3. 如果视频格式不一致：
   ```bash
   # 强制编码格式统一
   python video_contact.py -i /path/to/videos --force-encode
   ```

4. 如果旋转视频出现黑边：
   ```bash
   # 增加旋转时的放大比例
   python video_contact.py -i /path/to/videos --random-rotate --rotate-scale 2.0
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

- v1.2.0：增强功能
    - 添加随机镜像功能
    - 添加随机旋转功能
    - 改进音频处理
    - 添加视频补充模式选项

## 许可证

本项目采用 MIT 许可证。
