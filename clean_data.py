"""
╔══════════════════════════════════════════════════════╗
║       CLEAN DATA SCRIPT - GLOBAL FLUENT / TAP        ║
║   Xóa toàn bộ dữ liệu, chỉ giữ lại tài khoản Admin  ║
╚══════════════════════════════════════════════════════╝

Cách dùng:
    python clean_data.py

Lưu ý:
    - Script này sẽ XÓA VĨNH VIỄN toàn bộ dữ liệu user thường
    - Xóa luôn tất cả story topics và sessions
    - Chỉ giữ lại tài khoản có role='admin'
    - Bảng master data (vocabulary, grammar, achievement, cosmetic) KHÔNG bị xóa
"""

import sys
import os

# Đảm bảo chạy được từ thư mục gốc project
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.user import User

def confirm_action():
    print("\n" + "=" * 60)
    print("  CANH BAO TOI CAO - HANH DONG KHONG THE HOAN TAC")
    print("=" * 60)
    print("  Script nay se XOA VINH VIEN:")
    print("  x Tat ca tai khoan user thuong (giu admin)")
    print("  x Tat ca Story Topics (Text RPG Sinh Ton)")
    print("  x Tat ca Story Sessions")
    print("  x Lich su hoc tu vung (UserVocabulary)")
    print("  x Lich su ngu phap (UserGrammar)")
    print("  x Thanh tuu da dat (UserAchievement)")
    print("  x Lich su thi (TestLog)")
    print("  x Daily Quests")
    print("  x Notifications")
    print()
    print("  GIU NGUYEN: Vocabulary, Grammar, Achievement, Cosmetic")
    print("  GIU NGUYEN: Tai khoan Admin")
    print("=" * 60)
    
    answer = input("\n  Nhap 'XAC NHAN XOA' de tiep tuc: ").strip()
    if answer != "XAC NHAN XOA":
        print("\n  Da huy. Khong co du lieu nao bi xoa.")
        sys.exit(0)

def clean_all_data():
    confirm_action()
    
    app = create_app()
    with app.app_context():
        print("\n  Dang ket noi database...")
        
        deleted_counts = {}

        try:
            from app.models.story_session import StorySession
            count = StorySession.query.count()
            StorySession.query.delete()
            db.session.commit()
            deleted_counts["StorySession"] = count
            print(f"  OK Da xoa {count} Story Sessions")
        except Exception as e:
            db.session.rollback()
            print(f"  SKIP StorySession: {e}")

        try:
            from app.models.story_topic import StoryTopic
            count = StoryTopic.query.count()
            StoryTopic.query.delete()
            db.session.commit()
            deleted_counts["StoryTopic"] = count
            print(f"  OK Da xoa {count} Story Topics (RPG Sinh Ton)")
        except Exception as e:
            db.session.rollback()
            print(f"  SKIP StoryTopic: {e}")

        try:
            from app.models.user_vocabulary import UserVocabulary
            count = UserVocabulary.query.count()
            UserVocabulary.query.delete()
            db.session.commit()
            deleted_counts["UserVocabulary"] = count
            print(f"  OK Da xoa {count} ban ghi UserVocabulary")
        except Exception as e:
            db.session.rollback()
            print(f"  SKIP UserVocabulary: {e}")

        try:
            from app.models.user_grammar import UserGrammar
            count = UserGrammar.query.count()
            UserGrammar.query.delete()
            db.session.commit()
            deleted_counts["UserGrammar"] = count
            print(f"  OK Da xoa {count} ban ghi UserGrammar")
        except Exception as e:
            db.session.rollback()
            print(f"  SKIP UserGrammar: {e}")

        try:
            from app.models.user_achievement import UserAchievement
            count = UserAchievement.query.count()
            UserAchievement.query.delete()
            db.session.commit()
            deleted_counts["UserAchievement"] = count
            print(f"  OK Da xoa {count} ban ghi UserAchievement")
        except Exception as e:
            db.session.rollback()
            print(f"  SKIP UserAchievement: {e}")

        try:
            from app.models.test import TestLog
            count = TestLog.query.count()
            TestLog.query.delete()
            db.session.commit()
            deleted_counts["TestLog"] = count
            print(f"  OK Da xoa {count} ban ghi TestLog")
        except Exception as e:
            db.session.rollback()
            print(f"  SKIP TestLog: {e}")

        try:
            from app.models.daily_quest import DailyQuest
            count = DailyQuest.query.count()
            DailyQuest.query.delete()
            db.session.commit()
            deleted_counts["DailyQuest"] = count
            print(f"  OK Da xoa {count} ban ghi DailyQuest")
        except Exception as e:
            db.session.rollback()
            print(f"  SKIP DailyQuest: {e}")

        try:
            from app.models.notification import Notification
            count = Notification.query.count()
            Notification.query.delete()
            db.session.commit()
            deleted_counts["Notification"] = count
            print(f"  OK Da xoa {count} ban ghi Notification")
        except Exception as e:
            db.session.rollback()
            print(f"  SKIP Notification: {e}")

        try:
            from app.models.cosmetic import UserCosmetic
            count = UserCosmetic.query.count()
            UserCosmetic.query.delete()
            db.session.commit()
            deleted_counts["UserCosmetic"] = count
            print(f"  OK Da xoa {count} ban ghi UserCosmetic")
        except Exception as e:
            db.session.rollback()
            print(f"  SKIP UserCosmetic: {e}")

        try:
            from app.models.roadmap import UserMilestoneProgress
            count = UserMilestoneProgress.query.count()
            UserMilestoneProgress.query.delete()
            db.session.commit()
            deleted_counts["UserMilestoneProgress"] = count
            print(f"  OK Da xoa {count} ban ghi UserMilestoneProgress")
        except Exception as e:
            db.session.rollback()
            print(f"  SKIP UserMilestoneProgress: {e}")

        try:
            non_admins = User.query.filter(User.role != 'admin').all()
            count = len(non_admins)
            for u in non_admins:
                db.session.delete(u)
            db.session.commit()
            deleted_counts["User (non-admin)"] = count
            print(f"  OK Da xoa {count} tai khoan user thuong")
        except Exception as e:
            db.session.rollback()
            print(f"  FAIL User: {e}")

        admins = User.query.filter_by(role='admin').all()
        print("\n" + "=" * 60)
        print("  CLEAN DATA HOAN TAT")
        print("=" * 60)
        total = sum(deleted_counts.values())
        print(f"  Tong ban ghi da xoa: {total}")
        print(f"\n  Tai khoan Admin duoc giu lai ({len(admins)}):")
        for admin in admins:
            print(f"    -> @{admin.username} (ID: {admin.id})")
        print("=" * 60)

if __name__ == "__main__":
    clean_all_data()
