#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

compose_cmd() {
  if command -v docker &>/dev/null && docker compose version &>/dev/null; then
    echo "docker compose"
  elif command -v docker-compose &>/dev/null; then
    echo "docker-compose"
  else
    return 1
  fi
}

ensure_docker() {
  if ! command -v docker &>/dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
  fi
  if ! compose_cmd >/dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
  fi
}

run_compose() {
  local cmd
  cmd=$(compose_cmd)
  (cd "$SCRIPT_DIR" && $cmd "$@")
}

install_app() {
  ensure_docker
  if [ -z "${SECRET_KEY:-}" ]; then
    if command -v openssl &>/dev/null; then
      export SECRET_KEY=$(openssl rand -hex 32)
      echo "Generated SECRET_KEY: $SECRET_KEY"
      echo "Save this key for future reference."
    else
      echo "openssl not found. Please set SECRET_KEY manually."
    fi
  fi
  mkdir -p "$SCRIPT_DIR/data"
  echo "Building containers..."
  run_compose build
  echo "Starting containers..."
  run_compose up -d
  echo "PT Manager Pro is running at: http://localhost:8080"
}

start_app() {
  ensure_docker
  run_compose up -d
}

stop_app() {
  ensure_docker
  run_compose down
}

restart_app() {
  ensure_docker
  run_compose down
  run_compose up -d
}

update_app() {
  ensure_docker
  if [ -d "$SCRIPT_DIR/.git" ]; then
    echo "Updating repository from GitHub..."
    (
      cd "$SCRIPT_DIR"
      if git remote get-url origin &>/dev/null; then
        current_remote=$(git remote get-url origin)
        if [ "$current_remote" != "https://github.com/1336665/PT-Traffic-Toolkit.git" ]; then
          git remote set-url origin "https://github.com/1336665/PT-Traffic-Toolkit.git"
        fi
      else
        git remote add origin "https://github.com/1336665/PT-Traffic-Toolkit.git"
      fi
      current_branch=$(git rev-parse --abbrev-ref HEAD)
      git fetch origin "$current_branch"
      git reset --hard "origin/$current_branch"
      git clean -fd
    )
  else
    echo "Not a git repository. Please clone from https://github.com/1336665/PT-Traffic-Toolkit.git"
    exit 1
  fi
  run_compose build
  run_compose up -d
}

status_app() {
  ensure_docker
  run_compose ps
}

logs_app() {
  ensure_docker
  run_compose logs -f
}

show_menu() {
  echo ""
  echo "=========================================="
  echo "  PT Manager Pro 管理脚本"
  echo "=========================================="
  echo "1) 安装/初始化"
  echo "2) 启动"
  echo "3) 停止"
  echo "4) 重启"
  echo "5) 更新"
  echo "6) 状态"
  echo "7) 查看日志"
  echo "0) 退出"
  echo ""
}

while true; do
  show_menu
  read -rp "请选择操作: " choice
  case "$choice" in
    1) install_app ;;
    2) start_app ;;
    3) stop_app ;;
    4) restart_app ;;
    5) update_app ;;
    6) status_app ;;
    7) logs_app ;;
    0) exit 0 ;;
    *) echo "无效选择，请重试。" ;;
  esac
  echo ""
  read -rp "按回车返回菜单..." _
 done
