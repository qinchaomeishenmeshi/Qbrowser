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
        "--gpu-preset",
        choices=["p1", "p2", "p3", "p4", "p5", "p6", "p7"],
        default="p2",
        help="NVENC预设质量，p1最快但质量最低，p7最慢但质量最高",
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

        # 使用系统临时目录作为基础
        temp_base = Path(tempfile.gettempdir()) / "video_processor"
        temp_base.mkdir(exist_ok=True)
        self.temp_folder = temp_base / self.video_folder.name
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

        # 检查GPU可用性
        if self.use_gpu:
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

    def _get_audio_params(self):
        """根据质量设置选择音频参数"""
        if self.audio_quality == "fast":
            return ["-c:a", "libmp3lame", "-b:a", "96k", "-ar", "44100"]
        elif self.audio_quality == "normal":
            return ["-c:a", "aac", "-b:a", "128k", "-ar", "48000"]
        else:  # high
            return ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]

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
        """清理临时文件"""
        # 清理过时文件
        stale_files = [
            self.video_folder / "output_with_dots.mp4",
            self.video_folder / "output_with_overlays.mp4",
            self.concat_file,
        ]
        for stale_file in stale_files:
            if stale_file.exists():
                stale_file.unlink()

        # 清理临时拼接文件
        if self.temp_folder.exists():
            for f in self.temp_folder.glob(f"{self.temp_concat_prefix}*.mp4"):
                f.unlink()

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
        if not self.use_gpu:
            return [
                "-c:v",
                "libx264",
                "-preset",
                self.video_preset,
                "-crf",
                "23",
            ]

        if self.is_windows and self.encoder == "h264_nvenc":
            return [
                "-c:v",
                "h264_nvenc",
                "-preset",
                self.gpu_preset,
                "-rc",
                "vbr",
                "-cq",
                "23",
                "-b:v",
                "0",
            ]
        elif self.is_mac and self.encoder == "h264_videotoolbox":
            return [
                "-c:v",
                "h264_videotoolbox",
                "-b:v",
                "5000k",
                "-allow_sw",
                "1",
            ]
        else:
            return [
                "-c:v",
                "libx264",
                "-preset",
                self.video_preset,
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
                if duration > 0:
                    logger.info(f"跳过已存在文件: {dst.name} ({duration:.2f}s)")
                    self.skipped_count += 1
                    return dst, duration
            except Exception:
                pass

        # 强制统一尺寸 + 清除旋转元数据
        vf_scale = f"scale={self.output_width}:{self.output_height}:force_original_aspect_ratio=decrease,"
        vf_pad = f"pad={self.output_width}:{self.output_height}:(ow-iw)/2:(oh-ih)/2"

        # 构建命令
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-i",
            str(clip),
            *self._get_encode_params(),
            "-force_key_frames",
            "expr:gte(t,0)",
            *self.audio_params,
            "-movflags",
            "+faststart",
            "-vf",
            f"{vf_scale}{vf_pad}",
            "-metadata:s:v:0",
            "rotate=0",
            str(dst),
        ]

        progress_indicator = f"[{i + 1}/{self.total_clips}]"
        self.run_cmd(cmd, stage_desc=f"重编码 {progress_indicator}: {clip.name}")
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
        """并行重编码所有视频片段"""
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

        # 采样选择要处理的文件
        selected_files = self._sample_video_files(all_files)

        self.total_clips = len(selected_files)
        logger.info(f"找到 {len(all_files)} 个视频文件，将处理 {self.total_clips} 个")

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
                    batch = selected_files[i: i + batch_size]
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
                # 验证文件有效性
                duration = self.get_duration(batch_output)
                if duration > 0:
                    logger.info(f"跳过已存在批次: {batch_output.name}")
                    return batch_output
            except Exception:
                # 文件损坏，需要重新拼接
                pass

        inputs = []
        for clip in batch_clips:
            inputs += ["-i", str(clip)]

        # 简化的视频滤镜链
        video_filter = "".join(f"[{i}:v]" for i in range(len(batch_clips)))
        video_filter += f"concat=n={len(batch_clips)}:v=1:a=0[v]"

        # 简化音频处理 - 避免复杂的音频规范化处理
        audio_filter = "".join(f"[{i}:a]" for i in range(len(batch_clips)))
        audio_filter += f"concat=n={len(batch_clips)}:v=0:a=1[a]"

        filter_complex = f"{video_filter};{audio_filter}"

        cmd = (
                ["ffmpeg", "-nostdin", "-y"]
                + inputs
                + [
                    "-filter_complex",
                    filter_complex,
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
            batch_clips = clips[i: i + self.batch_size]
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
                    current_batches = batches[i: i + self.max_workers]
                    results = list(executor.map(self.process_batch, current_batches))
                    temp_concat_files.extend(results)

        # 最终合并所有批次
        self.final_concat(temp_concat_files)

    def _multi_level_concat(self, clips):
        """多级拼接处理大量文件"""
        # 一级拼接 - 每batch_size个文件一组
        level1_batches = []
        for i in range(0, len(clips), self.batch_size):
            batch_clips = clips[i: i + self.batch_size]
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
                batch_files = level1_files[i: i + batch_size]
                output_file = self.temp_folder / f"level2_batch_{i // batch_size:02d}.mp4"

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

        # 简化的拼接方式
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
        times = []
        step = random.randint(self.min_interval, self.max_interval)
        t = self.min_interval
        while t < dur:
            times.append(round(t, 2))
            t += step

        # 如果没有缩放点并且启用了预设缩放，添加中间点
        if not times and self.preset_zoom:
            times = [dur / 2]

        # 确保最后一个缩放效果持续到视频结束
        if times and times[-1] + self.zoom_duration < dur:
            times[-1] = dur - self.zoom_duration

        # 缩放位置选项
        positions = [
            (0, 0),  # 左上
            (w - w // self.zoom_scale, 0),  # 右上
            (0, h - h // self.zoom_scale),  # 左下
            (w - w // self.zoom_scale, h - h // self.zoom_scale),  # 右下
            ((w - w // self.zoom_scale) // 2, (h - h // self.zoom_scale) // 2),  # 中心
        ]

        # 构建滤镜链
        parts = []
        prev_label = "[0:v]"
        for i, start in enumerate(times):
            x, y = random.choice(positions)
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

        # 简化音频处理
        has_audio = self.has_audio_stream(self.concat_file)
        if has_audio:
            parts.append(f"[0:a]volume={self.audio_volume}[aout]")
            audio_map = ["-map", "[aout]"]
        else:
            parts.append("anullsrc=channel_layout=stereo:sample_rate=44100[aout]")
            audio_map = ["-map", "[aout]"]

        cmd = (
                [
                    "ffmpeg",
                    "-nostdin",
                    "-y",
                    "-i",
                    str(self.concat_file),
                    "-filter_complex",
                    ";".join(parts),
                    "-map",
                    map_label,
                ]
                + audio_map
                + [
                    "-c:v",
                    "libx264",
                    "-preset",
                    self.video_preset,
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    *self.audio_params,
                    "-shortest",
                    str(self.output_file),
                ]
        )
        self.run_cmd(cmd, stage_desc="缩放+音量处理")

    def append_concat_file(self):
        """直接添加已拼接的视频文件"""
        # 清除缓存确保获取最新时长
        self._duration_cache.clear()

        # 获取当前视频时长
        original_duration = self.get_duration(self.concat_file)
        temp_file = self.temp_folder / "temp_append.mp4"

        # 将当前文件与自身拼接
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-i",
            str(self.concat_file),
            "-i",
            str(self.concat_file),
            "-filter_complex",
            "concat=n=2:v=1:a=1[v][a]",
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
            str(temp_file),
        ]

        self.run_cmd(cmd, "整体视频拼接")

        # 验证新时长
        new_duration = self.get_duration(temp_file)
        if new_duration <= original_duration * 1.5:  # 检查是否真的增加了
            raise RuntimeError(
                f"拼接后时长不足预期: {original_duration:.2f}s -> {new_duration:.2f}s"
            )

        # 更新文件
        shutil.move(temp_file, self.concat_file)
        logger.info(
            f"整体拼接成功: {original_duration / 60:.2f}分钟 -> {new_duration / 60:.2f}分钟"
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
                logger.info(f"当前时长不足 {self.min_duration / 60:.2f}分钟，开始补充...")

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
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True
            )
            encoders = result.stdout.lower()

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
                else:
                    logger.warning("未检测到NVENC编码器支持，将使用CPU编码")
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

                    while current_dur < self.min_duration and tries < max_tries:
                        try:
                            logger.info(
                                f"当前总时长: {current_dur / 60:.2f}分钟，目标时长: {self.min_duration / 60:.2f}分钟，剩余: {(self.min_duration - current_dur) / 60:.2f}分钟"
                            )

                            # 使用整体拼接方法
                            new_dur = self.append_concat_file()
                            current_dur = new_dur
                            tries += 1

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

        except Exception as e:
            logger.error(f"处理失败: {e}")
            raise
        finally:
            elapsed = time.time() - overall_start
            logger.info(f"总耗时 {elapsed // 60:.0f}分{elapsed % 60:.0f}秒")

        return self.output_file


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
