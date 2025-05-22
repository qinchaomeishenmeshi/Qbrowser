import argparse
import logging
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psutil

# ------------------- 配置部分 -------------------
# 默认值，可通过命令行参数覆盖
DEFAULT_CONFIG = {
    "output_width": 720,
    "output_height": 1280,
    "min_interval": 60,  # 缩放效果最小间隔（秒）
    "max_interval": 120,  # 缩放效果最大间隔（秒）
    "zoom_scale": 2,  # 缩放比例
    "zoom_duration": 10,  # 缩放持续时间（秒）
    "audio_volume": 0.15,  # 最终音频音量比例
    "min_duration": 300,  # 最小总时长（秒）
    "preset_zoom": True,  # 是否在无缩放点时添加预设缩放点
    "batch_size": 5,  # 每批次处理的视频数量
    "max_workers": 0,  # 并行处理的最大工作线程数，0表示自动
    "skip_existing": True,  # 跳过已存在的编码文件
    "audio_quality": "fast",  # 音频质量模式: fast, normal, high
    "video_preset": "ultrafast",  # 视频编码预设: ultrafast, veryfast, medium
    "simple_concat": True,  # 是否使用简单拼接模式
    "force_encode": False,  # 是否强制统一编码格式
    "random_mirror": False,  # 是否随机对部分素材做镜像
    "mirror_ratio": 0.33,  # 镜像素材比例（0~1）
}

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("视频处理")

VIDEO_FOLDER = Path(r"D:\素材\5.13五香居素材\工厂生产")
TEMP_FOLDER = VIDEO_FOLDER / "__temp"
CONCAT_FILE = VIDEO_FOLDER / "__concat.mp4"
FINAL_FILE = VIDEO_FOLDER / "output_with_zoom.mp4"
TEMP_CONCAT_PREFIX = "temp_concat_"

# 音量比例，默认 15%
FINAL_AUDIO_VOLUME = 0.15
MIN_INTERVAL = 1 * 60
MAX_INTERVAL = 2 * 60
ZOOM_SCALE = 2
ZOOM_DURATION = 10
OUTPUT_WIDTH = 720
OUTPUT_HEIGHT = 1280
PRESET_ZOOM = True

MIN_TOTAL_DURATION = 5 * 60  # 最小总时长：1小时（秒）


# ------------------------------------------------


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="视频处理工具 - 缩放和拼接")
    parser.add_argument(
        "--input", "-i", type=str, required=True, help="输入视频文件夹路径"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="输出视频文件路径，默认为输入文件夹下的output_with_zoom.mp4",
    )
    parser.add_argument(
        "--width", type=int, default=DEFAULT_CONFIG["output_width"], help="输出视频宽度"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_CONFIG["output_height"],
        help="输出视频高度",
    )
    parser.add_argument(
        "--min-interval",
        type=int,
        default=DEFAULT_CONFIG["min_interval"],
        help="缩放效果最小间隔（秒）",
    )
    parser.add_argument(
        "--max-interval",
        type=int,
        default=DEFAULT_CONFIG["max_interval"],
        help="缩放效果最大间隔（秒）",
    )
    parser.add_argument(
        "--zoom-scale", type=int, default=DEFAULT_CONFIG["zoom_scale"], help="缩放比例"
    )
    parser.add_argument(
        "--zoom-duration",
        type=int,
        default=DEFAULT_CONFIG["zoom_duration"],
        help="缩放持续时间（秒）",
    )
    parser.add_argument(
        "--audio-volume",
        type=float,
        default=DEFAULT_CONFIG["audio_volume"],
        help="最终音频音量比例",
    )
    parser.add_argument(
        "--min-duration",
        type=int,
        default=DEFAULT_CONFIG["min_duration"],
        help="最小总时长（秒）",
    )
    parser.add_argument(
        "--no-preset-zoom",
        action="store_false",
        dest="preset_zoom",
        help="禁用预设缩放点",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_CONFIG["batch_size"],
        help="每批次处理的视频数量",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=DEFAULT_CONFIG["max_workers"],
        help="并行处理的最大工作线程数，0表示自动",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_false",
        dest="skip_existing",
        help="不跳过已存在的编码文件",
    )
    parser.add_argument(
        "--audio-quality",
        choices=["fast", "normal", "high"],
        default=DEFAULT_CONFIG["audio_quality"],
        help="音频质量模式",
    )
    parser.add_argument(
        "--video-preset",
        choices=["ultrafast", "veryfast", "fast", "medium"],
        default=DEFAULT_CONFIG["video_preset"],
        help="视频编码预设",
    )
    parser.add_argument(
        "--max-clips",
        type=int,
        default=0,
        help="最大处理片段数，0表示不限制。对于大量文件建议设置为20-50",
    )
    parser.add_argument(
        "--sample-strategy",
        choices=["random", "first", "duration", "all"],
        default="all",
        help="当文件超过最大处理数时的采样策略",
    )
    parser.add_argument(
        "--simple-concat",
        action="store_true",
        help="使用简单拼接模式（直接拼接，不重编码）",
    )
    parser.add_argument(
        "--force-encode", action="store_true", help="简单拼接模式下，强制统一编码格式"
    )
    parser.add_argument(
        "--use-gpu",
        action="store_true",
        help="使用GPU加速（需要NVIDIA显卡和NVENC支持）",
    )
    parser.add_argument(
        "--encoder",
        type=str,
        choices=["auto", "h264_nvenc", "h264_videotoolbox", "h264_qsv", "h264_amf", "libx264"],
        default="auto",
        help="指定编码器: auto-自动检测, h264_nvenc-NVIDIA, h264_videotoolbox-Mac, h264_qsv-Intel, h264_amf-AMD, libx264-CPU",
    )
    parser.add_argument(
        "--gpu-preset",
        choices=["p1", "p2", "p3", "p4", "p5", "p6", "p7"],
        default="p2",
        help="NVENC预设质量，p1最快但质量最低，p7最慢但质量最高",
    )
    parser.add_argument(
        "--random-mirror",
        action="store_true",
        help="随机对部分原始素材做左右镜像，镜像后的视频和原视频一起拼接",
    )
    parser.add_argument(
        "--mirror-ratio",
        type=float,
        default=DEFAULT_CONFIG["mirror_ratio"],
        help="随机镜像素材的比例（0~1），如0.5表示一半素材做镜像，默认0.33",
    )
    parser.add_argument(
        "--append-mode",
        choices=["random", "sequential", "alternating"],
        default="alternating",
        help="视频补充模式：random-随机补充，sequential-顺序补充，alternating-交替使用",
    )

    args = parser.parse_args()

    # 处理输出路径
    if not args.output:
        args.output = str(Path(args.input) / "output_with_zoom.mp4")

    # 自动计算worker数量
    if args.max_workers <= 0:
        # 获取可用CPU核心数
        cpu_count = psutil.cpu_count(logical=False) or 24  # i9-14900KF 有24核心
        mem_gb = psutil.virtual_memory().total / (1024 * 1024 * 1024)

        # 64GB内存优化：
        # FFmpeg进程约需要1-2GB内存，预留16GB给系统和其他进程
        available_mem_gb = mem_gb - 16
        mem_limit = max(1, int(available_mem_gb / 2))  # 每个进程预留2GB

        # i9-14900KF优化：
        # 对于简单拼接，可以使用更多核心
        if args.simple_concat:
            recommended_workers = min(cpu_count * 3 // 4, 18)  # 最多使用75%的核心
        else:
            # 转码时需要更多资源，稍微保守一些
            recommended_workers = min(cpu_count * 2 // 3, 16)  # 最多使用67%的核心

        # 考虑内存和CPU限制，取较小值
        args.max_workers = min(recommended_workers, mem_limit)

        # 64GB内存系统的优化设置：
        # 确保至少 6 个 worker，最多 18 个
        args.max_workers = max(6, min(18, args.max_workers))

        logger.info(
            f"自动设置并行处理线程数为: {args.max_workers} (内存: {mem_gb:.0f}GB)"
        )

    # 是否随机镜像
    args.random_mirror = getattr(args, "random_mirror", False)
    # 随机镜像素材的比例
    args.mirror_ratio = getattr(args, "mirror_ratio", DEFAULT_CONFIG["mirror_ratio"])
    # 视频补充模式
    args.append_mode = getattr(args, "append_mode", "alternating")

    return args


class VideoProcessor:
    """视频处理类"""

    def __init__(self, args):
        """初始化处理器"""
        self.video_folder = Path(args.input).resolve()
        self.output_file = (
            Path(args.output).resolve()
            if args.output
            else self.video_folder / "output_with_zoom.mp4"
        )

        # 临时目录直接放在当前素材文件夹下
        self.temp_folder = self.video_folder / "__temp"
        self.concat_file = self.temp_folder / "__concat.mp4"
        self.temp_concat_prefix = "temp_concat_"

        # 系统类型检测
        self.is_windows = sys.platform == "win32"
        self.is_mac = sys.platform == "darwin"

        # 配置参数
        self.output_width = args.width
        self.output_height = args.height
        self.min_interval = args.min_interval
        self.max_interval = args.max_interval
        self.zoom_scale = args.zoom_scale
        self.zoom_duration = args.zoom_duration
        self.audio_volume = args.audio_volume
        self.min_duration = args.min_duration
        self.preset_zoom = args.preset_zoom
        self.batch_size = args.batch_size
        self.max_workers = args.max_workers
        self.skip_existing = args.skip_existing
        self.audio_quality = args.audio_quality
        self.video_preset = args.video_preset
        self.max_clips = args.max_clips
        self.sample_strategy = args.sample_strategy
        self.is_simple_concat = args.simple_concat
        self.force_encode = args.force_encode

        # GPU相关配置
        self.use_gpu = args.use_gpu
        self.gpu_preset = args.gpu_preset
        # 用户指定的编码器选择
        self.encoder_choice = args.encoder

        # 检查GPU可用性
        if self.use_gpu or self.encoder_choice != "auto":
            self._check_gpu_availability()

        # 音频编码参数
        self.audio_params = self._get_audio_params()

        # 性能统计
        self.start_time = time.time()
        self.processed_count = 0
        self.skipped_count = 0

        # 缓存
        self._resolution_cache = {}
        self._duration_cache = {}

        # 随机镜像
        self.random_mirror = args.random_mirror
        # 随机镜像素材的比例
        self.mirror_ratio = args.mirror_ratio
        # 视频补充模式
        self.append_mode = args.append_mode

    def _get_audio_params(self):
        """根据质量设置选择音频参数"""
        # 基础音频参数，移除volume滤镜
        if self.audio_quality == "fast":
            return [
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-ar",
                "48000",
                "-ac",
                "2",  # 强制双声道
            ]
        elif self.audio_quality == "normal":
            return ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
        else:  # high
            return ["-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2"]

    def run_cmd(self, cmd, stage_desc=None):
        """执行命令并记录时间"""
        if stage_desc:
            logger.info(f"开始: {stage_desc}")
            start = time.time()

        try:
            # Windows系统编码处理
            encoding = "utf-8" if not self.is_windows else "gbk"

            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding=encoding,
                errors="replace",
            )
            if res.returncode:
                error_msg = res.stderr.strip()
                if self.is_windows:
                    # Windows下尝试转换编码
                    try:
                        error_msg = error_msg.encode("gbk").decode(
                            "utf-8", errors="replace"
                        )
                    except:
                        pass
                logger.error(f"命令执行失败: {error_msg}")
                raise RuntimeError(f"命令执行失败: {error_msg[:200]}...")

            if stage_desc:
                logger.info(f"完成: {stage_desc}，耗时 {time.time() - start:.2f}s")

            return res

        except Exception as e:
            if stage_desc:
                logger.error(f"{stage_desc} 失败: {str(e)}")
            raise

    def cleanup_temp(self):
        """清理临时文件和临时目录"""
        # 清理过时文件
        stale_files = [
            self.video_folder / "output_with_dots.mp4",
            self.video_folder / "output_with_overlays.mp4",
            self.concat_file,
        ]
        for stale_file in stale_files:
            if stale_file.exists():
                try:
                    stale_file.unlink()
                except Exception as e:
                    logger.warning(f"删除文件失败: {stale_file} {e}")

        # 删除整个临时目录
        if self.temp_folder.exists():
            try:
                shutil.rmtree(self.temp_folder)
                logger.info(f"已删除临时目录: {self.temp_folder}")
            except Exception as e:
                logger.warning(f"删除临时目录失败: {e}")

    def prepare_temp(self):
        """准备临时文件夹"""
        self.cleanup_temp()
        self.temp_folder.mkdir(parents=True, exist_ok=True)

        # Windows系统特殊处理：确保路径不超过最大长度
        if self.is_windows:
            try:
                self.temp_folder = Path(os.path.normpath(self.temp_folder))
                if len(str(self.temp_folder)) > 240:  # Windows路径长度限制
                    # 使用更短的临时路径
                    short_temp = Path(tempfile.gettempdir()) / "vp_tmp"
                    short_temp.mkdir(exist_ok=True)
                    self.temp_folder = short_temp
                    self.concat_file = self.temp_folder / "__concat.mp4"
                    logger.info(f"Windows系统：使用短临时路径 {self.temp_folder}")
            except Exception as e:
                logger.warning(f"临时文件夹路径处理警告: {e}")

    def has_audio_stream(self, path):
        """检查文件是否有音频流"""
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream=index",
                "-of",
                "csv=p=0",
                str(path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return bool(result.stdout.strip())

    def get_duration(self, path):
        """获取视频时长（带缓存）"""
        path_str = str(path)
        if path_str not in self._duration_cache:
            result = subprocess.check_output(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    path_str,
                ],
                text=True,
            ).strip()
            self._duration_cache[path_str] = float(result)
        return self._duration_cache[path_str]

    def detect_resolution(self, video_path):
        """检测视频分辨率（带缓存）"""
        path_str = str(video_path)
        if path_str not in self._resolution_cache:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=width,height",
                    "-of",
                    "csv=p=0",
                    path_str,
                ],
                capture_output=True,
                text=True,
            )
            width, height = map(int, result.stdout.strip().split(","))
            self._resolution_cache[path_str] = (width, height)
        return self._resolution_cache[path_str]

    def _get_encode_params(self):
        """获取编码参数"""
        # 使用已经由_check_gpu_availability设置好的self.encoder
        if self.use_gpu and hasattr(self, 'encoder'):
            encoder_type = self.encoder
            
            if encoder_type == "h264_nvenc":  # NVIDIA GPU
                logger.info("使用NVENC硬件加速编码")
                return [
                    "-c:v",
                    encoder_type,
                    "-preset",
                    self.gpu_preset,
                    "-pix_fmt",
                    "yuv420p",  # 强制使用 8 位颜色
                    "-rc",
                    "vbr",
                    "-cq",
                    "23",
                    "-b:v",
                    "0",
                    "-profile:v",
                    "high",
                    "-tune",
                    "hq",
                    "-spatial-aq",
                    "1",
                    "-temporal-aq",
                    "1",
                ]
            elif encoder_type == "h264_videotoolbox":  # macOS VideoToolbox
                logger.info("使用VideoToolbox硬件加速编码")
                return [
                    "-c:v",
                    encoder_type,
                    "-pix_fmt",
                    "yuv420p",
                    "-b:v",
                    "5M",
                    "-allow_sw",
                    "1",
                    "-profile:v",
                    "high",
                ]
            elif encoder_type == "h264_qsv":  # Intel QuickSync
                logger.info("使用Intel QuickSync硬件加速编码")
                return [
                    "-c:v",
                    encoder_type,
                    "-preset",
                    "medium",
                    "-pix_fmt",
                    "nv12",  # QSV通常使用nv12
                    "-global_quality",
                    "23",
                    "-look_ahead",
                    "1",
                ]
            elif encoder_type == "h264_amf":  # AMD AMF
                logger.info("使用AMD AMF硬件加速编码")
                return [
                    "-c:v",
                    encoder_type,
                    "-quality",
                    "quality",
                    "-pix_fmt",
                    "yuv420p",
                    "-rc",
                    "cqp",
                    "-qp_i",
                    "23",
                    "-qp_p",
                    "25",
                ]
            else:  # 其他硬件编码器
                logger.info(f"使用硬件编码器: {encoder_type}")
                return [
                    "-c:v",
                    encoder_type,
                    "-pix_fmt",
                    "yuv420p",
                ]
        
        # CPU编码参数（作为备选方案）
        logger.info("使用CPU编码 (libx264)")
        return [
            "-c:v",
            "libx264",
            "-preset",
            self.video_preset,
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "23",
        ]

    def reencode_clip(self, clip_info):
        """重编码单个视频片段（用于并行处理）"""
        i, clip = clip_info
        dst = self.temp_folder / f"clip_{i:03d}.mp4"

        # 跳过已存在的文件
        if self.skip_existing and dst.exists():
            try:
                duration = self.get_duration(dst)
                if duration > 0 and self.has_audio_stream(dst):
                    logger.info(f"跳过已存在文件: {dst.name} ({duration:.2f}s)")
                    self.skipped_count += 1
                    return dst, duration
            except Exception as e:
                logger.warning(f"检查文件失败: {e}")

        # 获取源文件音频信息
        has_audio = self.has_audio_stream(clip)
        logger.info(f"处理文件 {clip.name} - {'有' if has_audio else '无'}音频流")

        # 构建基础命令
        cmd = ["ffmpeg", "-nostdin", "-y", "-i", str(clip)]

        # 如果没有音频，添加静音源
        if not has_audio:
            cmd.extend(
                [
                    "-f",
                    "lavfi",
                    "-i",
                    "anullsrc=channel_layout=stereo:sample_rate=48000",
                ]
            )

        # 构建滤镜链
        vfilters = []
        rotation = self._get_video_rotation(clip)
        if rotation:
            vfilters.append(f"transpose={1 if rotation == 90 else 2}")

        target_width = self.output_width
        target_height = self.output_height
        if rotation in [90, 270]:
            target_width, target_height = target_height, target_width

        vfilters.extend(
            [
                f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease",
                f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2",
            ]
        )

        # 添加编码参数
        cmd.extend(self._get_encode_params())

        # 添加音频参数
        if has_audio:
            cmd.extend(
                [
                    "-map",
                    "0:v:0",  # 第一个输入的视频流
                    "-map",
                    "0:a:0?",  # 第一个输入的音频流（如果存在）
                    *self._get_audio_params(),
                ]
            )
        else:
            cmd.extend(
                [
                    "-map",
                    "0:v:0",  # 第一个输入的视频流
                    "-map",
                    "1:a:0",  # 第二个输入（静音源）的音频流
                    *self._get_audio_params(),
                    "-shortest",  # 确保视频和音频长度匹配
                ]
            )

        # 添加视频滤镜
        if vfilters:
            cmd.extend(["-vf", ",".join(vfilters)])

        # 添加输出文件
        cmd.extend(["-movflags", "+faststart", "-metadata:s:v:0", "rotate=0", str(dst)])

        progress_indicator = f"[{i + 1}/{self.total_clips}]"
        self.run_cmd(cmd, stage_desc=f"重编码 {progress_indicator}: {clip.name}")

        # 验证输出文件
        if not self.has_audio_stream(dst):
            logger.error(f"错误：输出文件 {dst.name} 没有音频流！")
            raise RuntimeError(f"音频处理失败: {dst.name}")

        self.processed_count += 1

        # 计算预计剩余时间
        elapsed = time.time() - self.start_time
        clips_left = self.total_clips - (self.processed_count + self.skipped_count)
        if self.processed_count > 0 and clips_left > 0:
            avg_time = elapsed / self.processed_count
            eta = avg_time * clips_left
            logger.info(
                f"进度: {self.processed_count}/{self.total_clips} 已处理，"
                f"{self.skipped_count} 已跳过，预计剩余时间: {eta // 60:.0f}分{eta % 60:.0f}秒"
            )

        return dst, self.get_duration(dst)

    def _get_video_rotation(self, video_path):
        """获取视频旋转角度"""
        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream_tags=rotate",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            rotation = result.stdout.strip()

            if rotation:
                return int(rotation)

            # 检查显示矩阵
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream_side_data=displaymatrix",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if "rotation of 90.00 degrees" in result.stdout:
                return 90
            elif "rotation of 270.00 degrees" in result.stdout:
                return 270
            elif "rotation of 180.00 degrees" in result.stdout:
                return 180

        except Exception as e:
            logger.warning(f"获取视频旋转信息失败: {e}")

        return 0

    def _sample_video_files(self, video_files):
        """根据采样策略选择要处理的视频文件"""
        if self.max_clips <= 0 or len(video_files) <= self.max_clips:
            # 如果未设置最大数量限制，或者文件数量未超过限制，返回所有文件
            return video_files

        logger.info(
            f"文件数量 ({len(video_files)}) 超过最大处理限制 ({self.max_clips})，采用 {self.sample_strategy} 策略采样"
        )

        if self.sample_strategy == "random":
            # 随机采样
            return random.sample(video_files, self.max_clips)

        elif self.sample_strategy == "first":
            # 取前N个
            return video_files[: self.max_clips]

        elif self.sample_strategy == "duration":
            # 获取时长并排序，优先选择较长的视频
            files_with_duration = []
            for file in video_files:
                try:
                    duration = self.get_duration(file)
                    files_with_duration.append((file, duration))
                except Exception:
                    # 如果无法获取时长，设为0
                    files_with_duration.append((file, 0))

            # 按时长降序排序
            files_with_duration.sort(key=lambda x: x[1], reverse=True)

            # 返回时长最长的N个文件
            return [f[0] for f in files_with_duration[: self.max_clips]]

        # 默认返回所有文件
        return video_files

    def reencode_clips(self):
        """并行重编码所有视频片段，并根据配置随机镜像部分素材"""
        logger.info("步骤1：重编码所有视频片段")

        # 过滤出有效视频文件
        all_files = sorted(
            [
                f
                for f in self.video_folder.iterdir()
                if f.suffix.lower() in [".mp4", ".mov", ".avi"]
                and not f.name.startswith(("__", "output_with"))
            ]
        )

        if not all_files:
            raise ValueError(f"未在 {self.video_folder} 找到视频文件")

        # ===== 新增：随机镜像部分素材 =====
        mirror_files = []
        if getattr(self, "random_mirror", False):
            logger.info("启用随机镜像功能，部分素材将被左右翻转")
            import random

            mirror_count = max(1, int(len(all_files) * self.mirror_ratio))
            mirror_indices = set(random.sample(range(len(all_files)), mirror_count))
            for idx in mirror_indices:
                src = all_files[idx]
                mirrored = self.temp_folder / (src.stem + "_mirrored" + src.suffix)
                if not mirrored.exists():
                    self.mirror_video(str(src), str(mirrored))
                mirror_files.append(mirrored)
            logger.info(
                f"已生成 {len(mirror_files)} 个镜像素材 (比例: {self.mirror_ratio})"
            )
        # ====== 结束 ======

        # 采样选择要处理的文件
        selected_files = self._sample_video_files(all_files)
        # 合并镜像素材
        if mirror_files:
            selected_files = list(selected_files) + mirror_files

        self.total_clips = len(selected_files)
        logger.info(
            f"找到 {len(all_files)} 个视频文件，将处理 {self.total_clips} 个（含镜像）"
        )

        # 重置统计信息
        self.start_time = time.time()
        self.processed_count = 0
        self.skipped_count = 0

        # 串行或并行处理视频重编码
        temp_clips, durations = [], []
        if self.max_workers <= 1:
            # 单线程处理
            for i, clip in enumerate(selected_files):
                clip, duration = self.reencode_clip((i, clip))
                temp_clips.append(clip)
                durations.append(duration)
        else:
            # 使用线程池并行处理，但限制批次大小防止内存溢出
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                batch_size = 20  # 每批处理20个文件
                for i in range(0, len(selected_files), batch_size):
                    batch = selected_files[i : i + batch_size]
                    results = list(
                        executor.map(self.reencode_clip, enumerate(batch, i))
                    )

                    for clip, duration in results:
                        temp_clips.append(clip)
                        durations.append(duration)

        logger.info(
            f"完成重编码: {self.processed_count} 个处理，{self.skipped_count} 个跳过"
        )
        return temp_clips, durations

    def process_batch(self, batch_info):
        """处理单个批次的拼接"""
        batch_index, batch_clips = batch_info
        batch_output = (
            self.temp_folder / f"{self.temp_concat_prefix}{batch_index:02d}.mp4"
        )

        # 跳过已存在的文件
        if self.skip_existing and batch_output.exists():
            try:
                duration = self.get_duration(batch_output)
                if duration > 0:
                    logger.info(f"跳过已存在批次: {batch_output.name}")
                    return batch_output
            except Exception:
                pass

        inputs = []
        for clip in batch_clips:
            inputs += ["-i", str(clip)]

        # 构建滤镜链
        filter_parts = []
        # 1. 构建输入标签部分
        for i in range(len(batch_clips)):
            filter_parts.append(f"[{i}:v][{i}:a]")

        # 2. 添加concat滤镜，输出到临时标签
        filter_parts.append(f"concat=n={len(batch_clips)}:v=1:a=1[v][a];")

        # 3. 添加音量调整滤镜
        filter_parts.append(f"[a]volume={self.audio_volume}[aout]")

        filter_complex = "".join(filter_parts)

        cmd = (
            ["ffmpeg", "-nostdin", "-y"]
            + inputs
            + [
                "-filter_complex",
                filter_complex,
                "-map",
                "[v]",
                "-map",
                "[aout]",
                *self._get_encode_params(),
                *self.audio_params,
                str(batch_output),
            ]
        )
        self.run_cmd(cmd, stage_desc=f"批次拼接 #{batch_index + 1}")
        return batch_output

    def concat_with_xfade(self, clips):
        """批量拼接函数（优化处理大量文件）"""
        logger.info("步骤2：分批次拼接视频")

        # 如果文件太多，需要分多级处理
        if len(clips) > 50:
            logger.info(f"文件数量较多 ({len(clips)}个)，采用多级处理")
            return self._multi_level_concat(clips)

        # 准备批次
        batches = []
        for i in range(0, len(clips), self.batch_size):
            batch_clips = clips[i : i + self.batch_size]
            batches.append((i // self.batch_size, batch_clips))

        # 处理批次
        temp_concat_files = []
        if len(batches) == 1 or self.max_workers <= 1:
            # 单线程处理
            for batch in batches:
                result = self.process_batch(batch)
                temp_concat_files.append(result)
        else:
            # 并行处理批次，但限制同时处理的批次数
            with ThreadPoolExecutor(
                max_workers=min(len(batches), self.max_workers)
            ) as executor:
                for i in range(0, len(batches), self.max_workers):
                    current_batches = batches[i : i + self.max_workers]
                    results = list(executor.map(self.process_batch, current_batches))
                    temp_concat_files.extend(results)

        # 最终合并所有批次
        self.final_concat(temp_concat_files)

    def _multi_level_concat(self, clips):
        """多级拼接处理大量文件"""
        # 一级拼接 - 每batch_size个文件一组
        level1_batches = []
        for i in range(0, len(clips), self.batch_size):
            batch_clips = clips[i : i + self.batch_size]
            level1_batches.append((i // self.batch_size, batch_clips))

        # 处理一级批次
        level1_files = []
        total_batches = len(level1_batches)

        logger.info(f"第一级拼接: 处理 {total_batches} 个批次")
        for i, batch in enumerate(level1_batches):
            output_file = self.process_batch(batch)
            level1_files.append(output_file)
            logger.info(f"第一级进度: {i + 1}/{total_batches}")

        # 如果一级拼接结果还是很多，继续二级拼接
        if len(level1_files) > 10:
            logger.info(f"执行第二级拼接: 将 {len(level1_files)} 个文件合并为更大的块")
            level2_batches = []
            batch_size = min(10, len(level1_files) // 3)  # 合适的二级批次大小

            for i in range(0, len(level1_files), batch_size):
                batch_files = level1_files[i : i + batch_size]
                output_file = (
                    self.temp_folder / f"level2_batch_{i // batch_size:02d}.mp4"
                )

                # 合并这批文件
                self._concat_files(batch_files, output_file)
                level2_batches.append(output_file)

            # 最终合并所有二级批次
            self.final_concat(level2_batches)
        else:
            # 直接合并一级批次
            self.final_concat(level1_files)

    def _concat_files(self, input_files, output_file):
        """合并多个文件，用于多级拼接"""
        if len(input_files) == 1:
            shutil.copy(input_files[0], output_file)
            return

        inputs = []
        for file in input_files:
            inputs += ["-i", str(file)]

        # 使用简化的拼接方式
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-y",
            *inputs,
            "-filter_complex",
            f"concat=n={len(input_files)}:v=1:a=1[v][a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-preset",
            self.video_preset,
            "-crf",
            "23",
            *self.audio_params,
            str(output_file),
        ]

        self.run_cmd(cmd, stage_desc=f"合并 {len(input_files)} 个文件")

    def final_concat(self, input_files):
        """最终合并所有批次"""
        logger.info(f"步骤3：合并 {len(input_files)} 个批次")

        if len(input_files) == 1:
            # 只有一个文件时直接复制
            shutil.copy(input_files[0], self.concat_file)
            logger.info("只有一个批次，直接复制为最终文件")
            return

        inputs = []
        for file in input_files:
            inputs += ["-i", str(file)]

        # 构建滤镜链
        filter_parts = []
        # 1. 构建输入标签部分
        for i in range(len(input_files)):
            filter_parts.append(f"[{i}:v][{i}:a]")

        # 2. 添加concat滤镜，输出到临时标签
        filter_parts.append(f"concat=n={len(input_files)}:v=1:a=1[v][a];")

        # 3. 添加音量调整滤镜
        filter_parts.append(f"[a]volume={self.audio_volume}[aout]")

        filter_complex = "".join(filter_parts)

        cmd = [
            "ffmpeg",
            "-nostdin",
            "-y",
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "[aout]",
            *self._get_encode_params(),
            *self.audio_params,
            str(self.concat_file),
        ]
        self.run_cmd(cmd, stage_desc="最终合并")

    def apply_zoom(self):
        """添加放大效果"""
        logger.info("步骤4：添加放大效果")

        # 获取视频信息
        w, h = self.detect_resolution(self.concat_file)
        dur = self.get_duration(self.concat_file)

        # 生成缩放时间点
        self.zoom_times = []
        step = random.randint(self.min_interval, self.max_interval)
        t = self.min_interval
        while t < dur:
            self.zoom_times.append(round(t, 2))
            t += step

        # 如果没有缩放点并且启用了预设缩放，添加中间点
        if not self.zoom_times and self.preset_zoom:
            self.zoom_times = [dur / 2]

        # 确保最后一个缩放效果持续到视频结束
        if self.zoom_times and self.zoom_times[-1] + self.zoom_duration < dur:
            self.zoom_times[-1] = dur - self.zoom_duration

        # 缩放位置选项
        self.zoom_positions = [
            (0, 0),  # 左上
            (w - w // self.zoom_scale, 0),  # 右上
            (0, h - h // self.zoom_scale),  # 左下
            (w - w // self.zoom_scale, h - h // self.zoom_scale),  # 右下
            ((w - w // self.zoom_scale) // 2, (h - h // self.zoom_scale) // 2),  # 中心
        ]

        # 构建滤镜链
        parts = []
        prev_label = "[0:v]"
        for i, start in enumerate(self.zoom_times):
            x, y = random.choice(self.zoom_positions)
            parts.append(
                f"[0:v]crop={w // self.zoom_scale}:{h // self.zoom_scale}:{x}:{y},scale={w}:{h}[z{i}]"
            )
            logger.info(f"缩放时间点: {start:.2f}s, 位置: ({x}, {y})")
            enable_expr = f"between(t,{start},{start + self.zoom_duration})"
            parts.append(f"{prev_label}[z{i}]overlay=0:0:enable='{enable_expr}'[v{i}]")
            prev_label = f"[v{i}]"

        # 强制末尾帧刷新
        parts.append(f"{prev_label}trim=0:{dur},setpts=PTS-STARTPTS[zoomed]")
        if self.output_width and self.output_height:
            parts.append(
                f"[zoomed]scale={self.output_width}:{self.output_height}[final]"
            )
            map_label = "[final]"
        else:
            map_label = "[zoomed]"

        # 修改音频处理部分，确保音频存在且音量适当
        has_audio = self.has_audio_stream(self.concat_file)
        if has_audio:
            # 确保明确复制音频流
            parts.append(f"[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume={self.audio_volume}[aout]")
            audio_map = ["-map", "[aout]"]
            audio_params = ["-c:a", "aac", "-b:a", "192k", "-ac", "2"]
        else:
            # 生成静音
            parts.append(f"anullsrc=channel_layout=stereo:sample_rate=48000,atrim=duration={dur}[aout]")
            audio_map = ["-map", "[aout]"]
            audio_params = ["-c:a", "aac", "-b:a", "128k"]
        
        # 添加调试日志
        logger.info(f"音频状态: {'有音频流' if has_audio else '无音频流'}, 音量: {self.audio_volume}")
        
        cmd = [
            "ffmpeg", "-nostdin", "-y",
            "-i", str(self.concat_file),
            "-filter_complex", ";".join(parts),
            "-map", map_label,
        ] + audio_map + [
            *self._get_encode_params(),
            *audio_params,
            "-shortest",
            str(self.output_file),
        ]
        
        # 输出完整命令方便调试
        logger.debug(f"缩放处理命令: {' '.join(cmd)}")
        self.run_cmd(cmd, stage_desc="缩放+音量处理")

    def append_concat_file(self, clips=None, append_mode='random'):
        """使用重编码好的素材线性补充视频时长
        
        Args:
            clips: 已重编码的素材列表，如果为None则使用保存的素材
            append_mode: 'random' 随机选择素材，'sequential' 顺序选择素材
        """
        # 清除缓存确保获取最新时长
        self._duration_cache.clear()
        
        # 如果没有提供clips，使用已保存的素材
        if clips is None and hasattr(self, '_encoded_clips'):
            clips = self._encoded_clips
        
        # 如果仍然没有可用的clips，报错
        if not clips or len(clips) == 0:
            raise ValueError("没有可用的素材进行补充，请先重编码素材")
        
        # 获取当前视频时长
        original_duration = self.get_duration(self.concat_file)
        temp_file = self.temp_folder / "temp_append.mp4"
        
        # 获取命令行参数或使用传入的模式
        actual_mode = append_mode
        
        # 根据模式选择素材
        selected_clips = []
        if actual_mode == 'random':
            # 随机选择1-3个素材
            num_to_select = min(random.randint(1, 3), len(clips))
            selected_clips = random.sample(clips, num_to_select)
            logger.info(f"随机选择了 {num_to_select} 个素材")
        else:  # sequential模式
            # 使用轮询方式选择下一个素材
            if not hasattr(self, '_append_index'):
                self._append_index = 0
            selected_clips = [clips[self._append_index % len(clips)]]
            self._append_index += 1
            logger.info(f"顺序选择了第 {self._append_index-1} 个素材")
        
        logger.info(f"使用{actual_mode}模式补充 {len(selected_clips)} 个素材")
        
        # 构建命令：将原始文件和选定的素材拼接
        inputs = ["-i", str(self.concat_file)]
        for clip in selected_clips:  # 使用筛选后的素材列表
            inputs.extend(["-i", str(clip)])
            logger.info(f"添加素材: {clip}")
        
        # 构建滤镜链
        n_inputs = 1 + len(selected_clips)  # 修正：使用selected_clips的长度
        filter_complex = f"concat=n={n_inputs}:v=1:a=1[v][a];[a]volume={self.audio_volume}[aout]"
        
        cmd = [
            "ffmpeg", "-nostdin", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[v]", 
            "-map", "[aout]",
            *self._get_encode_params(),
            *self.audio_params,
            str(temp_file),
        ]
        
        self.run_cmd(cmd, f"{actual_mode}模式素材补充")
        
        # 验证新时长
        new_duration = self.get_duration(temp_file)
        if new_duration <= original_duration * 1.05:  # 检查是否真的增加了
            logger.warning(f"拼接后时长几乎没有增加: {original_duration:.2f}s -> {new_duration:.2f}s")
        
        # 更新文件
        shutil.move(temp_file, self.concat_file)
        logger.info(
            f"素材补充成功: {original_duration / 60:.2f}分钟 -> {new_duration / 60:.2f}分钟"
        )
        
        # 清除缓存
        self._duration_cache.clear()
        
        return new_duration

    def simple_concat(self):
        """简单拼接实现（支持最小时长要求）"""
        logger.info("使用简单拼接模式")

        # 获取所有视频文件
        video_files = sorted(
            [
                f
                for f in self.video_folder.iterdir()
                if f.suffix.lower() in [".mp4", ".mov", ".avi"]
                and not f.name.startswith(("__", "output_with"))
            ]
        )

        if not video_files:
            raise ValueError(f"未在 {self.video_folder} 找到视频文件")

        # 创建临时文件夹
        self.prepare_temp()

        try:
            # 第一次拼接
            initial_output = self._do_simple_concat(video_files)
            current_duration = self.get_duration(initial_output)
            logger.info(f"初始拼接时长: {current_duration / 60:.2f}分钟")

            # 检查是否需要补充时长
            if current_duration < self.min_duration:
                logger.info(
                    f"当前时长不足 {self.min_duration / 60:.2f}分钟，开始补充..."
                )

                tries = 0
                max_tries = 100

                while current_duration < self.min_duration and tries < max_tries:
                    try:
                        # 创建新的拼接列表
                        temp_output = self.temp_folder / f"temp_concat_{tries}.mp4"

                        # 将当前文件和原始文件再次拼接
                        files_to_concat = [initial_output] + video_files
                        self._do_simple_concat(files_to_concat, temp_output)

                        # 检查新时长
                        new_duration = self.get_duration(temp_output)
                        if new_duration <= current_duration:
                            raise RuntimeError("拼接后时长未增加")

                        # 更新文件和时长
                        shutil.move(temp_output, initial_output)
                        current_duration = new_duration
                        logger.info(f"当前总时长: {current_duration / 60:.2f}分钟")

                    except Exception as e:
                        logger.error(f"补充拼接失败: {e}")
                        tries += 1
                        continue

                    tries += 1

                if current_duration < self.min_duration:
                    logger.warning(
                        f"已达到最大尝试次数或无法继续增加时长，"
                        f"最终时长: {current_duration / 60:.2f}分钟"
                    )

            # 移动到最终输出位置
            shutil.move(initial_output, self.output_file)
            logger.info(f"拼接完成，最终时长: {current_duration / 60:.2f}分钟")

        finally:
            # 清理临时文件
            self.cleanup_temp()

    def _do_simple_concat(self, video_files, output_file=None):
        """执行简单拼接的核心逻辑"""
        if output_file is None:
            output_file = self.temp_folder / "temp_concat_initial.mp4"

        concat_list = self.temp_folder / "concat_list.txt"

        # 检查格式兼容性
        if not self.force_encode:
            formats = set()
            for file in video_files:
                format_info = self._get_format_info(file)
                formats.add(format_info)
                if len(formats) > 1:
                    logger.warning(
                        "检测到不同格式的视频文件，建议使用 --force-encode 参数进行格式统一"
                    )
                    raise ValueError("视频格式不一致，无法直接拼接")

        if self.force_encode:
            # 统一编码格式
            logger.info("统一编码格式...")
            encoded_files = []
            for i, file in enumerate(video_files):
                output = self.temp_folder / f"encoded_{i:03d}{Path(file).suffix}"
                if not (self.skip_existing and output.exists()):
                    self._encode_video(file, output)
                encoded_files.append(output)
            video_files = encoded_files

        # 创建concat列表文件
        with open(concat_list, "w", encoding="utf-8") as f:
            for file in video_files:
                f.write(f"file '{file.absolute()}'\n")

        # 执行拼接
        logger.info(f"开始拼接 {len(video_files)} 个文件...")
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(output_file),
        ]
        self.run_cmd(cmd, "简单拼接")

        return output_file

    def _get_format_info(self, file):
        """获取视频格式信息"""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height,r_frame_rate",
            "-of",
            "csv=p=0",
            str(file),
        ]
        return self.run_cmd(cmd).stdout.strip()

    def _encode_video(self, input_file, output_file):
        """统一视频编码格式"""
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_file),
            *self._get_encode_params(),
            *self.audio_params,
            str(output_file),
        ]
        self.run_cmd(cmd, f"编码: {input_file.name}")

    def _check_gpu_availability(self):
        """检查GPU/硬件编码器是否可用"""
        try:
            # 获取所有可用编码器
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True
            )
            encoders = result.stdout.lower()
            
            # 如果用户指定了编码器（非auto），优先使用
            if hasattr(self, 'encoder_choice') and self.encoder_choice != "auto":
                user_encoder = self.encoder_choice
                
                # 检查用户指定的编码器是否可用
                if user_encoder in encoders:
                    logger.info(f"使用用户指定的编码器: {user_encoder}")
                    self.encoder = user_encoder
                    # 如果是硬件编码器，则设置GPU标志
                    self.use_gpu = user_encoder != "libx264"
                    return
                else:
                    logger.warning(f"用户指定的编码器 {user_encoder} 不可用，将尝试自动检测")
            
            # 自动检测模式
            # 检查系统类型
            if self.is_mac:  # macOS
                if "h264_videotoolbox" in encoders:
                    self.use_gpu = True
                    self.encoder = "h264_videotoolbox"
                    logger.info("检测到VideoToolbox编码器支持，将使用Mac硬件加速")
                else:
                    logger.warning("未检测到VideoToolbox编码器支持，将使用CPU编码")
                    self.use_gpu = False
                    self.encoder = "libx264"
            else:
                # 其他系统（Windows/Linux）
                if "h264_nvenc" in encoders:
                    self.use_gpu = True
                    self.encoder = "h264_nvenc"
                    logger.info("检测到NVENC编码器支持，将使用GPU加速")
                elif "h264_qsv" in encoders:  # Intel QuickSync
                    self.use_gpu = True
                    self.encoder = "h264_qsv"
                    logger.info("检测到Intel QuickSync支持，将使用硬件加速")
                elif "h264_amf" in encoders:  # AMD
                    self.use_gpu = True
                    self.encoder = "h264_amf"
                    logger.info("检测到AMD AMF支持，将使用硬件加速")
                else:
                    logger.warning("未检测到硬件编码器支持，将使用CPU编码")
                    self.use_gpu = False
                    self.encoder = "libx264"
        except Exception as e:
            logger.warning(f"硬件编码器检查失败: {e}，将使用CPU编码")
            self.use_gpu = False
            self.encoder = "libx264"

    def process(self):
        """执行完整处理流程"""
        overall_start = time.time()

        try:
            if self.is_simple_concat:
                # 使用简单拼接模式
                self.simple_concat()
            else:
                self.prepare_temp()
                # 步骤1：重编码源视频
                clips, durations = self.reencode_clips()
                
                # 保存重编码的素材，供后续补充使用
                self._encoded_clips = clips

                # 步骤2：初始拼接
                self.concat_with_xfade(clips)
                current_dur = self.get_duration(self.concat_file)
                logger.info(f"初始拼接时长: {current_dur / 60:.2f}分钟")

                # 步骤3：智能补充循环
                if current_dur < self.min_duration:
                    logger.info(
                        f"当前时长 {current_dur / 60:.2f}分钟 < 目标时长 {self.min_duration / 60:.2f}分钟，开始补充"
                    )

                    # 保存初始拼接结果备份
                    initial_concat = self.temp_folder / "initial_concat.mp4"
                    shutil.copy(self.concat_file, initial_concat)

                    tries = 0
                    max_tries = 100
                    
                    # 获取命令行参数指定的补充模式
                    user_append_mode = getattr(self, 'append_mode', 'alternating')
                    
                    # 根据用户设置决定补充模式
                    if user_append_mode == 'alternating':
                        # 交替模式
                        current_mode = 'random'
                        alternate = True
                    else:
                        # 固定模式
                        current_mode = user_append_mode
                        alternate = False
                    
                    while current_dur < self.min_duration and tries < max_tries:
                        try:
                            logger.info(
                                f"当前总时长: {current_dur / 60:.2f}分钟，目标时长: {self.min_duration / 60:.2f}分钟，剩余: {(self.min_duration - current_dur) / 60:.2f}分钟"
                            )

                            # 使用修改后的补充方法
                            new_dur = self.append_concat_file(self._encoded_clips,append_mode=current_mode)
                            current_dur = new_dur
                            tries += 1
                            
                            # 只有在交替模式时才切换
                            if alternate:
                                current_mode = 'sequential' if current_mode == 'random' else 'random'

                        except Exception as e:
                            logger.error(f"补充拼接失败: {e}")
                            tries += 1

                    if tries >= max_tries and current_dur < self.min_duration:
                        logger.warning(
                            f"已到达最大尝试次数 {max_tries}，停止补充。最终时长: {current_dur / 60:.2f}分钟"
                        )
                else:
                    logger.info(
                        f"当前时长 {current_dur / 60:.2f}分钟 已达目标时长，跳过补充"
                    )

                # 步骤4：添加缩放效果
                self.apply_zoom()

                logger.info(
                    f"最终视频参数：{self.output_width}x{self.output_height} {current_dur:.2f}s"
                )

                # 在process方法的最后一步前添加
                if not self.has_audio_stream(self.concat_file):
                    logger.warning("警告：拼接后的文件没有音频流，最终视频可能无声")

        except Exception as e:
            logger.error(f"处理失败: {e}")
            raise
        finally:
            elapsed = time.time() - overall_start
            logger.info(f"总耗时 {elapsed // 60:.0f}分{elapsed % 60:.0f}秒")

        return self.output_file

    def mirror_video(self, input_file: str, output_file: str = None) -> str:
        """
        对指定视频文件进行左右镜像（水平翻转），输出到output_file。
        如果output_file未指定，则在原文件名后加_mirrored后缀。
        返回输出文件路径。
        """
        input_path = Path(input_file)
        if output_file is None:
            output_path = input_path.with_name(
                input_path.stem + "_mirrored" + input_path.suffix
            )
        else:
            output_path = Path(output_file)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vf",
            "hflip",
            "-c:a",
            "copy",
            str(output_path),
        ]
        self.run_cmd(cmd, stage_desc=f"左右镜像: {input_path.name}")
        return str(output_path)


def main():
    """主函数"""
    try:
        # 检测是否有psutil模块，如果没有则使用默认值
        try:
            import psutil
        except ImportError:
            logger.warning("未安装psutil模块，使用默认并行度设置")

        args = parse_args()
        processor = VideoProcessor(args)
        output_file = processor.process()
        logger.info(f"处理完成! 输出文件: {output_file}")
    except Exception as e:
        logger.error(f"处理失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
