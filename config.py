import argparse
import torch
from multiprocessing import cpu_count


def config_file_change_fp32():
    for config_file in ["32k.json", "40k.json", "48k.json"]:
        with open(f"configs/{config_file}", "r") as f:
            strr = f.read().replace("true", "false")
        with open(f"configs/{config_file}", "w") as f:
            f.write(strr)
    with open("trainset_preprocess_pipeline_print.py", "r") as f:
        strr = f.read().replace("3.7", "3.0")
    with open("trainset_preprocess_pipeline_print.py", "w") as f:
        f.write(strr)


class Config:
    def __init__(self):
        self.device = "cuda:0"
        self.is_half = True
        self.n_cpu = 0
        self.gpu_name = None
        self.gpu_mem = None
        (
            self.python_cmd,
            self.listen_port,
            self.iscolab,
            self.noparallel,
            self.noautoopen,
        ) = self.arg_parse()
        self.x_pad, self.x_query, self.x_center, self.x_max = self.device_config()

    @staticmethod
    def arg_parse() -> tuple:
        parser = argparse.ArgumentParser()
        parser.add_argument("--port", type=int, default=7865, help="Listen port")
        parser.add_argument(
            "--pycmd", type=str, default="python", help="Python command"
        )
        parser.add_argument("--colab", action="store_true", help="Launch in colab")
        parser.add_argument(
            "--noparallel", action="store_true", help="Disable parallel processing"
        )
        parser.add_argument(
            "--noautoopen",
            action="store_true",
            help="Do not open in browser automatically",
        )
        cmd_opts = parser.parse_args()

        cmd_opts.port = cmd_opts.port if 0 <= cmd_opts.port <= 65535 else 7865

        return (
            cmd_opts.pycmd,
            cmd_opts.port,
            cmd_opts.colab,
            cmd_opts.noparallel,
            cmd_opts.noautoopen,
        )

    def device_config(self) -> tuple:
        if torch.cuda.is_available():
            i_device = int(self.device.split(":")[-1])
            self.gpu_name = torch.cuda.get_device_name(i_device)
            if (
                ("16" in self.gpu_name and "V100" not in self.gpu_name.upper())
                or "P40" in self.gpu_name.upper()
                or "1060" in self.gpu_name
                or "1070" in self.gpu_name
                or "1080" in self.gpu_name
            ):
                print("16系/10系显卡和P40强制单精度")
                self.is_half = False
                config_file_change_fp32()
            else:
                self.gpu_name = None
            self.gpu_mem = int(
                torch.cuda.get_device_properties(i_device).total_memory
                / 1024
                / 1024
                / 1024
                + 0.4
            )
            if self.gpu_mem <= 4:
                with open("trainset_preprocess_pipeline_print.py", "r") as f:
                    strr = f.read().replace("3.7", "3.0")
                with open("trainset_preprocess_pipeline_print.py", "w") as f:
                    f.write(strr)
        elif torch.backends.mps.is_available():
            print("没有发现支持的N卡, 使用MPS进行推理")
            self.device = "mps"
            self.is_half = False
            config_file_change_fp32()
        else:
            print("没有发现支持的N卡, 使用CPU进行推理")
            self.device = "cpu"
            self.is_half = False
            config_file_change_fp32()

        if self.n_cpu == 0:
            self.n_cpu = cpu_count()

        if self.is_half:
            # 6G显存配置
            x_pad = 3
            x_query = 10
            x_center = 60
            x_max = 65
        else:
            # 5G显存配置
            x_pad = 1
            x_query = 6
            x_center = 38
            x_max = 41

        if self.gpu_mem != None and self.gpu_mem <= 4:
            x_pad = 1
            x_query = 5
            x_center = 30
            x_max = 32

        return x_pad, x_query, x_center, x_max
