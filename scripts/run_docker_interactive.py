#!/usr/bin/env python3
import os
import subprocess
import sys

def get_input_path(prompt, required=False):
    while True:
        path = input(prompt).strip()
        if not path:
            if required:
                print("此项为必填项，请重新输入。")
                continue
            return None
        
        # Expand user path (~/)
        abs_path = os.path.abspath(os.path.expanduser(path))
        if os.path.exists(abs_path):
            return abs_path
        else:
            print(f"❌ 路径不存在: {abs_path}")
            create = input("是否自动创建该目录? (y/n) [y]: ").strip().lower()
            if create != 'n':
                try:
                    os.makedirs(abs_path, exist_ok=True)
                    print(f"✅ 已创建目录: {abs_path}")
                    return abs_path
                except Exception as e:
                    print(f"❌ 创建失败: {e}")
            
            if not required:
                retry = input("是否重试? (y/n) [y]: ").strip().lower()
                if retry == 'n':
                    return None

def main():
    print("==========================================")
    print("🐳 Maim Workspace Docker 交互式启动脚本 (v2)")
    print("==========================================")
    print("此脚本将帮助您挂载本地配置文件并启动 Docker 容器。")
    print("将统一挂载数据目录，实现数据库文件的隔离存储：")
    print("  - MaimConfig & MaiMBot: {data_dir}/shared/MaiBot.db (Shared)")
    print("  - WebBackend:           {data_dir}/web/maim_web.db")
    print("")

    # 1. Image Name
    image_name = "maim_workspace_monolith"
    container_name = "maim_monolith"

    # Template directory path (relative to this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    template_dir = os.path.join(project_root, "template")
    
    # Working config directory for user
    config_work_dir = os.path.join(os.getcwd(), "config")
    os.makedirs(config_work_dir, exist_ok=True)

    def get_path_or_template(prompt_text, template_name, target_name):
        user_path = get_input_path(prompt_text)
        if user_path:
            return user_path
        
        # Try to use template
        tpl_path = os.path.join(template_dir, template_name)
        if os.path.exists(tpl_path):
            target_path = os.path.join(config_work_dir, target_name)
            if not os.path.exists(target_path):
                print(f"ℹ️ 未提供路径，正在从模板生成: {target_path}")
                try:
                    import shutil
                    shutil.copy2(tpl_path, target_path)
                    print(f"✅ 已生成默认配置: {target_path} (建议稍后修改)")
                except Exception as e:
                    print(f"❌ 无法复制模板: {e}")
                    return None
            else:
                print(f"ℹ️ 使用已存在的默认配置: {target_path}")
            return target_path
        else:
            print(f"⚠️ 未找到模板文件: {tpl_path}")
            return None

    # 2. Config Paths
    print("\n--- 配置文件设置 ---")
    model_config_path = get_path_or_template(
        "请输入本地 model_config.toml 路径 (回车自动生成): ", 
        "model_config.toml", 
        "model_config.toml"
    )
    bot_config_path = get_path_or_template(
        "请输入本地 bot_config.toml 路径 (回车自动生成): ", 
        "bot_config.toml", 
        "bot_config.toml"
    )
    env_file_path = get_path_or_template(
        "请输入本地 MaiMBot .env 文件路径 (回车自动生成): ", 
        ".env", 
        ".env"
    )
    maimconfig_env_path = get_path_or_template(
        "请输入本地 MaimConfig .env 文件路径 (回车自动生成): ",
        "maimconfig.env",
        "maimconfig.env"
    )

    # 3. Data Persistence
    print("\n--- 数据持久化设置 ---")
    print("挂载本地目录到容器的 /workspace/data。")
    data_dir = get_input_path("请输入本地数据目录路径 (推荐 ./docker_data) [回车默认使用 ./data]: ")
    
    if not data_dir:
        # Default to ./data if not provided
        data_dir = os.path.abspath("./data")
        os.makedirs(data_dir, exist_ok=True)
        print(f"使用默认数据目录: {data_dir}")

    # 4. Construct Command
    cmd = [
        "docker", "run", "-it", 
        "-p", "8000:8000",
        "-p", "8880:8880",
        "-p", "5173:5173",
        "-p", "8090:8090",
        "--name", container_name,
    ]

    # Mounts
    if model_config_path:
        cmd.extend(["-v", f"{model_config_path}:/workspace/MaiMBot/config/model_config.toml"])
        print(f"✅ 将挂载 model_config: {model_config_path}")
    
    if bot_config_path:
        cmd.extend(["-v", f"{bot_config_path}:/workspace/MaiMBot/config/bot_config.toml"])
        print(f"✅ 将挂载 bot_config: {bot_config_path}")

    if env_file_path:
        cmd.extend(["-v", f"{env_file_path}:/workspace/MaiMBot/.env"])
        print(f"✅ 将挂载 MaiMBot .env: {env_file_path}")

    if maimconfig_env_path:
        cmd.extend(["-v", f"{maimconfig_env_path}:/workspace/MaimConfig/.env"])
        print(f"✅ 将挂载 MaimConfig .env: {maimconfig_env_path}")

    # Unified Data Mount
    cmd.extend(["-v", f"{data_dir}:/workspace/data"])
    print(f"✅ 将挂载数据目录: {data_dir} -> /workspace/data")
    
    # Unified Data Mount
    cmd.extend(["-v", f"{data_dir}:/workspace/data"])
    print(f"✅ 将挂载数据目录: {data_dir} -> /workspace/data")
    
    # Environment Variables for Path Resolution
    cmd.extend([
        "-e", "MAIMBOT_MODEL_CONFIG_PATH=/workspace/MaiMBot/config/model_config.toml",
        "-e", "MAIMBOT_BOT_CONFIG_TEMPLATE_PATH=/workspace/MaiMBot/template/bot_config_template.toml"
    ])

    # Mount Startup Script (Hotfix)
    start_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "start_all_docker.sh"))
    cmd.extend(["-v", f"{start_script}:/workspace/start_all_docker.sh"])
    print(f"✅ 将挂载启动脚本: {start_script} -> /workspace/start_all_docker.sh")
    
    # Check if image exists
    print(f"\n🔍 检查 Docker 镜像: {image_name}")
    image_check = subprocess.run(
        f"docker images -q {image_name}", 
        shell=True, 
        capture_output=True, 
        text=True
    )
    
    if not image_check.stdout.strip():
        print(f"⚠️ 镜像 {image_name} 不存在，正在为您自动构建 (这可能需要几分钟)...")
        print("------------------------------------------")
        docker_build_cmd = ["docker", "build", "-t", image_name, "."]
        try:
            # Build from project root
            subprocess.run(docker_build_cmd, cwd=project_root, check=True)
            print("✅ 镜像构建成功！")
        except subprocess.CalledProcessError:
            print("❌ 镜像构建失败，请检查 Dockerfile。")
            sys.exit(1)
    else:
        print("✅ 镜像已存在，跳过构建。")

    cmd.append(image_name)

    # 5. Clean up old container
    print("\n--- 正在清理旧容器 ---")
    subprocess.run(f"docker rm -f {container_name} || true", shell=True)

    # 6. Run
    print(f"\n🚀 正在启动容器...\n执行命令: {' '.join(cmd)}\n")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n已停止启动。")

if __name__ == "__main__":
    main()
