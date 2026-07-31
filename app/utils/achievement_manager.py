from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement
from app.models.user import User
from app.models.notification import Notification  # Bổ sung import Model Notification
from app import db


def check_and_unlock_achievements(user_id, event_type, current_value):
    """
    Hàm kiểm tra và mở khóa thành tựu.
    event_type: 'STREAK' (Điểm danh), 'GACHA_COMBO' (Chuỗi vô cực), 'LEVEL' (Level hiện tại)
    """
    unlocked_new = []

    # Lấy các thành tựu liên quan đến event này mà user chưa có
    subquery = db.session.query(UserAchievement.achievement_id).filter_by(user_id=user_id)
    potential_achievements = Achievement.query.filter(
        Achievement.condition_type == event_type,
        Achievement.condition_value <= current_value,
        ~Achievement.id.in_(subquery)
    ).all()

    if not potential_achievements:
        return unlocked_new

    user = User.query.get(user_id)

    for ach in potential_achievements:
        # Cấp thành tựu
        new_ua = UserAchievement(user_id=user_id, achievement_id=ach.id)
        db.session.add(new_ua)

        # Thưởng xu
        user.coins += ach.reward_coins

        # -----> HỆ THỐNG BẮN THÔNG BÁO TỰ ĐỘNG <-----
        notif = Notification(
            user_id=user_id,
            title="THÀNH TỰU MỚI",
            message=f"Mở khóa: {ach.title} (+{ach.reward_coins} Xu)",
            type="ACHIEVEMENT"
        )
        db.session.add(notif)

        unlocked_new.append({
            "title": ach.title,
            "reward": ach.reward_coins,
            "icon": ach.icon_url
        })

    db.session.commit()
    return unlocked_new