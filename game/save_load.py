"""游戏存档管理"""
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from game.state import GameState
from config import SAVE_DIR, DEFAULT_SAVE_FILE

os.makedirs(SAVE_DIR, exist_ok=True)


def save_game(state: GameState, filepath: str = DEFAULT_SAVE_FILE) -> None:
    Path(filepath).write_text(state.model_dump_json(indent=2), encoding="utf-8")


def load_game(filepath: str = DEFAULT_SAVE_FILE) -> GameState | None:
    p = Path(filepath)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return GameState(**data)


def list_saves() -> List[Dict]:
    """列出所有存档及其元数据"""
    saves = []
    save_dir = Path(SAVE_DIR)
    
    for save_file in save_dir.glob("*.json"):
        try:
            data = json.loads(save_file.read_text(encoding="utf-8"))
            
            # 获取文件修改时间
            mtime = datetime.fromtimestamp(save_file.stat().st_mtime)
            
            saves.append({
                "filename": save_file.name,
                "filepath": str(save_file),
                "ruler_name": data.get("ruler_name", "未知"),
                "turn": data.get("turn", 0),
                "phase": data.get("phase", "未知"),
                "save_time": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": mtime.timestamp()
            })
        except Exception as e:
            print(f"读取存档 {save_file.name} 失败: {e}")
    
    # 按保存时间倒序排列
    saves.sort(key=lambda x: x["timestamp"], reverse=True)
    return saves


def delete_save(filepath: str) -> bool:
    """删除指定存档"""
    try:
        path = Path(filepath)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception as e:
        print(f"删除存档失败: {e}")
        return False


def save_game_with_slot(state: GameState, slot_name: str) -> None:
    """保存到指定存档槽位"""
    filename = f"{slot_name}.json"
    filepath = os.path.join(SAVE_DIR, filename)
    save_game(state, filepath)


def load_game_from_slot(slot_name: str) -> GameState | None:
    """从指定存档槽位加载"""
    filename = f"{slot_name}.json"
    filepath = os.path.join(SAVE_DIR, filename)
    return load_game(filepath)
