from flask import Blueprint, jsonify, request, session, render_template
from datetime import datetime, timedelta
import random

from app import db
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app.models.user_vocabulary import UserVocabulary
from app.models.farm import FarmCrop, FarmPlot, FarmInventory
from app.utils.pixel_art_crops import CROPS_PIXEL_DATA, get_crop_svg

farm_bp = Blueprint('farm_bp', __name__, url_prefix='/api/game/farm')

# Danh mục 5 loại vật phẩm hỗ trợ giảm thời gian & tăng thưởng
FARM_SHOP_ITEMS = [
    {
        "code": "fert_speed_25",
        "name": "Phân Bón Hữu Cơ Sinh Học",
        "name_en": "Organic Speed Fertilizer",
        "type": "FERTILIZER",
        "price": 10,
        "effect_desc": "Rút ngắn 25% thời gian sinh trưởng còn lại của cây",
        "icon_badge": "⚡ 25%"
    },
    {
        "code": "fert_speed_50",
        "name": "Phân Bón Tăng Tốc Turbo NPK",
        "name_en": "Turbo Growth NPK",
        "type": "FERTILIZER",
        "price": 25,
        "effect_desc": "Rút ngắn 50% thời gian sinh trưởng còn lại",
        "icon_badge": "⚡ 50%"
    },
    {
        "code": "fert_speed_75",
        "name": "Tinh Chất Siêu Sinh Trưởng Hyper",
        "name_en": "Hyper-Growth Elixir",
        "type": "FERTILIZER",
        "price": 45,
        "effect_desc": "Rút ngắn 75% thời gian sinh trưởng của cây",
        "icon_badge": "⚡ 75%"
    },
    {
        "code": "magic_water_instant",
        "name": "Bình Nước Suối Thần Kỳ",
        "name_en": "Miracle Spring Dew",
        "type": "BOOSTER",
        "price": 70,
        "effect_desc": "Kích thích cây chín và sẵn sàng thu hoạch NGAY LẬP TỨC 100%!",
        "icon_badge": "🌟 100%"
    },
    {
        "code": "fert_golden_double",
        "name": "Phân Bón Hoàng Kim Bội Thu",
        "name_en": "Golden Yield Compost",
        "type": "BOOSTER",
        "price": 60,
        "effect_desc": "Rút ngắn 50% thời gian + NHÂN ĐÔI số lượng Từ Vựng & Xu khi thu hoạch",
        "icon_badge": "✨ 2X"
    }
]

# Thông số khởi tạo 20 loại cây trồng
INITIAL_CROPS = [
    # Common (A1)
    {"code": "crop_radish", "name": "Củ Cải Khởi Đầu", "name_en": "Radish of Dawn", "rarity": "COMMON", "cefr_level": "A1", "seed_price": 5, "harvest_coins": 12, "harvest_rp": 5, "growth_seconds": 30, "vocab_count": 1, "description": "Củ cải đỏ tươi giòn ngọt, mầm non mở đầu cho hành trình khám phá từ vựng A1 hàng ngày."},
    {"code": "crop_carrot", "name": "Cà Rốt Tinh Anh", "name_en": "Insight Carrot", "rarity": "COMMON", "cefr_level": "A1", "seed_price": 8, "harvest_coins": 18, "harvest_rp": 8, "growth_seconds": 45, "vocab_count": 1, "description": "Cà rốt cam thon nhọn, bổ sung thị lực và trí nhớ từ vựng đồ vật cơ bản."},
    {"code": "crop_potato", "name": "Khoai Tây Bền Bỉ", "name_en": "Sturdy Potato", "rarity": "COMMON", "cefr_level": "A1", "seed_price": 12, "harvest_coins": 25, "harvest_rp": 10, "growth_seconds": 60, "vocab_count": 1, "description": "Khoai tây bùi béo giàu năng lượng, giúp xây dựng gốc rễ từ vựng đời sống vững chắc."},
    {"code": "crop_corn", "name": "Bắp Ngô Nắng Ấm", "name_en": "Golden Sweetcorn", "rarity": "COMMON", "cefr_level": "A1", "seed_price": 15, "harvest_coins": 32, "harvest_rp": 12, "growth_seconds": 75, "vocab_count": 1, "description": "Từng hạt ngô vàng mọng hấp thụ ánh nắng sớm, mở khóa từ vựng thời tiết và tự nhiên."},
    {"code": "crop_pea", "name": "Đậu Hà Lan Tươi", "name_en": "Fresh Pea Pod", "rarity": "COMMON", "cefr_level": "A1", "seed_price": 18, "harvest_coins": 38, "harvest_rp": 15, "growth_seconds": 90, "vocab_count": 1, "description": "Vỏ đậu xanh mở ra những hạt từ vựng gia đình và cảm xúc ấm áp."},

    # Uncommon (A2)
    {"code": "crop_tomato", "name": "Cà Chua Mọng Nước", "name_en": "Ruby Tomato", "rarity": "UNCOMMON", "cefr_level": "A2", "seed_price": 25, "harvest_coins": 55, "harvest_rp": 20, "growth_seconds": 150, "vocab_count": 1, "description": "Cà chua đỏ rực rỡ như ngọc ruby, mang đến từ vựng du lịch và phương tiện giao thông."},
    {"code": "crop_onion", "name": "Hành Tây Cú Pháp", "name_en": "Layered Onion", "rarity": "UNCOMMON", "cefr_level": "A2", "seed_price": 30, "harvest_coins": 68, "harvest_rp": 22, "growth_seconds": 180, "vocab_count": 1, "description": "Nhiều lớp hương vị đan xen, giúp bóc tách các tầng nghĩa từ vựng công việc và mua sắm."},
    {"code": "crop_strawberry", "name": "Dâu Tây Ngữ Nghĩa", "name_en": "Sweet Strawberry", "rarity": "UNCOMMON", "cefr_level": "A2", "seed_price": 35, "harvest_coins": 80, "harvest_rp": 25, "growth_seconds": 210, "vocab_count": 1, "description": "Vị ngọt dịu quyến rũ, mở khóa kho từ vựng sở thích, văn hóa và lễ hội."},
    {"code": "crop_pepper", "name": "Ớt Chuông Rực Lửa", "name_en": "Blazing Bell Pepper", "rarity": "UNCOMMON", "cefr_level": "A2", "seed_price": 40, "harvest_coins": 92, "harvest_rp": 28, "growth_seconds": 240, "vocab_count": 1, "description": "Màu sắc rực rỡ tiếp lửa động lực, bổ sung từ vựng sức khỏe và thể thao năng động."},
    {"code": "crop_eggplant", "name": "Cà Tím Huyền Diệu", "name_en": "Mystic Eggplant", "rarity": "UNCOMMON", "cefr_level": "A2", "seed_price": 45, "harvest_coins": 105, "harvest_rp": 30, "growth_seconds": 270, "vocab_count": 1, "description": "Sắc tím hoàng gia quý phái, khai phá từ vựng công nghệ và truyền thông sơ cấp."},

    # Rare (B1)
    {"code": "crop_sunflower", "name": "Hoa Hướng Dương Tri Thức", "name_en": "Scholar Sunflower", "rarity": "RARE", "cefr_level": "B1", "seed_price": 60, "harvest_coins": 140, "harvest_rp": 40, "growth_seconds": 360, "vocab_count": 2, "description": "Luôn hướng về ánh mặt trời chân lý, gặt hái từ vựng học thuật và nghiên cứu B1."},
    {"code": "crop_pumpkin", "name": "Bí Ngô Hoàng Kim", "name_en": "Royal Pumpkin", "rarity": "RARE", "cefr_level": "B1", "seed_price": 75, "harvest_coins": 175, "harvest_rp": 45, "growth_seconds": 480, "vocab_count": 2, "description": "Thành quả tròn trịa sau chuỗi ngày vun xới, trao tặng từ vựng môi trường và xã hội."},
    {"code": "crop_mushroom", "name": "Nấm Dạ Quang Oxford", "name_en": "Luminous Morel", "rarity": "RARE", "cefr_level": "B1", "seed_price": 90, "harvest_coins": 210, "harvest_rp": 50, "growth_seconds": 600, "vocab_count": 2, "description": "Tự phát sáng huyền ảo trong đêm, mở lối cho từ vựng kinh tế và thương mại B1."},
    {"code": "crop_grape", "name": "Chùm Nho Thạch Anh", "name_en": "Amethyst Grape", "rarity": "RARE", "cefr_level": "B1", "seed_price": 110, "harvest_coins": 250, "harvest_rp": 55, "growth_seconds": 720, "vocab_count": 2, "description": "Từng quả nho tím biếc óng ánh, chắt lọc tinh hoa từ vựng truyền thông đại chúng."},

    # Epic (B2)
    {"code": "crop_lotus", "name": "Sen Ngọc Bích Tri Giác", "name_en": "Jade Lotus", "rarity": "EPIC", "cefr_level": "B2", "seed_price": 140, "harvest_coins": 320, "harvest_rp": 70, "growth_seconds": 960, "vocab_count": 2, "description": "Thanh khiết vươn lên từ bùn lầy, thấu suốt từ vựng tư duy phản biện và tâm lý học B2."},
    {"code": "crop_dragon", "name": "Thanh Long Hỏa Diệm", "name_en": "Dragon Pearl", "rarity": "EPIC", "cefr_level": "B2", "seed_price": 170, "harvest_coins": 390, "harvest_rp": 80, "growth_seconds": 1200, "vocab_count": 2, "description": "Mang khí phách của loài rồng lửa, chứa đựng kho từ vựng khoa học tự nhiên và vũ trụ."},
    {"code": "crop_crystal", "name": "Hoa Pha Lê Hàn Băng", "name_en": "Frost Crystal Bloom", "rarity": "EPIC", "cefr_level": "B2", "seed_price": 200, "harvest_coins": 460, "harvest_rp": 90, "growth_seconds": 1440, "vocab_count": 2, "description": "Kết tinh từ băng tuyết vĩnh cửu, khai phá từ vựng pháp lý, ngoại giao và triết luận."},

    # Legendary (C1/C2)
    {"code": "crop_tree", "name": "Nhánh Cây Thế Giới Yggdrasil", "name_en": "Branch of Yggdrasil", "rarity": "LEGENDARY", "cefr_level": "C1", "seed_price": 250, "harvest_coins": 580, "harvest_rp": 120, "growth_seconds": 1800, "vocab_count": 3, "description": "Rễ đâm sâu vào cội nguồn ngôn ngữ, kết trái những từ vựng hàn lâm C1 siêu cao cấp."},
    {"code": "crop_apple", "name": "Táo Vàng Trí Tuệ Vô Tận", "name_en": "Infinity Golden Apple", "rarity": "LEGENDARY", "cefr_level": "C1", "seed_price": 320, "harvest_coins": 750, "harvest_rp": 150, "growth_seconds": 2400, "vocab_count": 3, "description": "Trái cấm của miền tri thức vô biên, mở khóa các khái niệm triết học trừu tượng đỉnh cao."},
    {"code": "crop_nebula", "name": "Hoa Hồng Tinh Vân C2", "name_en": "Cosmic Nebula Rose", "rarity": "LEGENDARY", "cefr_level": "C2", "seed_price": 400, "harvest_coins": 999, "harvest_rp": 200, "growth_seconds": 3000, "vocab_count": 3, "description": "Nở rộ giữa dải ngân hà huyền bí, ban tặng từ vựng văn học cổ điển C2 - Độc Cô Cầu Bại."}
]


# Cấu hình gia súc nông trại & thời gian Cooldown nhận thưởng
ANIMAL_CONFIGS = {
    "cow": {
        "name": "Bò Sữa Holstein",
        "action_title": "Vắt Sữa",
        "icon": "🥛",
        "badge_ready": "🥛 VẮT SỮA: SẴN SÀNG",
        "reward_coins": 10,
        "reward_rp": 5,
        "cooldown_seconds": 60,
        "ready_msg": "🐮 Bò Sữa Holstein: \"Úm bò bòòò~ Vừa vắt được xô sữa tươi béo ngậy! (+10 Xu, +5 RP)\""
    },
    "chicken": {
        "name": "Gà Mái Hoa Mơ",
        "action_title": "Nhặt Trứng",
        "icon": "🧺",
        "badge_ready": "🧺 NHẶT TRỨNG: SẴN SÀNG",
        "reward_coins": 8,
        "reward_rp": 3,
        "cooldown_seconds": 45,
        "ready_msg": "🐔 Gà Mái Hoa Mơ: \"Cục ta cục tác! Nhặt được giỏ trứng gà tươi vàng ươm! (+8 Xu, +3 RP)\""
    },
    "pig": {
        "name": "Heo Con Ủn Ỉn",
        "action_title": "Chăm Sóc",
        "icon": "🥓",
        "badge_ready": "🥓 CHO ĂN: SẴN SÀNG",
        "reward_coins": 12,
        "reward_rp": 6,
        "cooldown_seconds": 90,
        "ready_msg": "🐷 Heo Con Ủn Ỉn: \"Ụt ịt ụt ịt~ Heo con no nê cảm ơn bạn chăm sóc! (+12 Xu, +6 RP)\""
    }
}

# Bộ lưu trữ mốc thời gian tương tác gần nhất của từng user: {(user_id, animal): datetime}
_ANIMAL_LAST_INTERACTIONS = {}

def get_animals_state_for_user(user_id: int) -> dict:
    """Trả về trạng thái cooldown & sẵn sàng cho từng con vật của người dùng"""
    now = datetime.now()
    res = {}
    for code, cfg in ANIMAL_CONFIGS.items():
        last_time = _ANIMAL_LAST_INTERACTIONS.get((user_id, code))
        if not last_time:
            remaining = 0
        else:
            elapsed = (now - last_time).total_seconds()
            remaining = max(0, int(cfg["cooldown_seconds"] - elapsed))

        res[code] = {
            "name": cfg["name"],
            "action_title": cfg["action_title"],
            "icon": cfg["icon"],
            "reward_coins": cfg["reward_coins"],
            "reward_rp": cfg["reward_rp"],
            "cooldown_seconds": cfg["cooldown_seconds"],
            "remaining_seconds": remaining,
            "is_ready": (remaining == 0)
        }
    return res


def ensure_farm_initialized(user_id: int):
    """Đảm bảo danh mục 20 loại cây trồng và các ô đất của người dùng đã được khởi tạo"""
    # 1. Khởi tạo danh mục 20 cây nếu chưa có trong DB
    if FarmCrop.query.count() < 20:
        for c in INITIAL_CROPS:
            existing = FarmCrop.query.get(c["code"])
            if not existing:
                crop_obj = FarmCrop(
                    code=c["code"],
                    name=c["name"],
                    name_en=c["name_en"],
                    rarity=c["rarity"],
                    cefr_level=c["cefr_level"],
                    seed_price=c["seed_price"],
                    harvest_coins=c["harvest_coins"],
                    harvest_rp=c["harvest_rp"],
                    growth_seconds=c["growth_seconds"],
                    vocab_count=c["vocab_count"],
                    description=c["description"]
                )
                db.session.add(crop_obj)
        db.session.commit()

    # 2. Khởi tạo 6 ô đất cho người dùng nếu chưa có
    user_plots = FarmPlot.query.filter_by(user_id=user_id).all()
    if len(user_plots) < 6:
        existing_indices = {p.plot_index for p in user_plots}
        plot_configs = [
            {"index": 0, "unlocked": True, "cost": 0},
            {"index": 1, "unlocked": True, "cost": 0},
            {"index": 2, "unlocked": True, "cost": 0},
            {"index": 3, "unlocked": False, "cost": 40},
            {"index": 4, "unlocked": False, "cost": 80},
            {"index": 5, "unlocked": False, "cost": 150},
        ]
        for cfg in plot_configs:
            if cfg["index"] not in existing_indices:
                new_plot = FarmPlot(
                    user_id=user_id,
                    plot_index=cfg["index"],
                    is_unlocked=cfg["unlocked"],
                    unlock_cost=cfg["cost"]
                )
                db.session.add(new_plot)

        # 3. Tặng gói hạt giống tân thủ nếu kho chưa có gì
        existing_inv = FarmInventory.query.filter_by(user_id=user_id).first()
        if not existing_inv:
            starter_items = [
                FarmInventory(user_id=user_id, item_type='SEED', item_code='seed_crop_radish', quantity=3),
                FarmInventory(user_id=user_id, item_type='SEED', item_code='seed_crop_carrot', quantity=2),
                FarmInventory(user_id=user_id, item_type='FERTILIZER', item_code='fert_speed_25', quantity=2),
            ]
            db.session.bulk_save_objects(starter_items)

        db.session.commit()


@farm_bp.route('/state', methods=['GET'])
def get_farm_state():
    """Lấy toàn bộ trạng thái khu vườn, ô đất và kho của người chơi"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

    ensure_farm_initialized(user_id)

    plots = FarmPlot.query.filter_by(user_id=user_id).order_by(FarmPlot.plot_index).all()
    plots_data = []
    for p in plots:
        pd = p.to_dict()
        # Đính kèm SVG 3D theo trạng thái (kích thước chuẩn 96px nổi bật)
        pd["pixel_art_svg"] = get_crop_svg(p.crop_code, pd["stage"], size=96)
        plots_data.append(pd)

    inventory = FarmInventory.query.filter_by(user_id=user_id).all()
    inv_data = {
        "seeds": [],
        "boosters": []
    }
    for item in inventory:
        if item.quantity > 0:
            if item.item_type == 'SEED':
                crop_code = item.item_code.replace('seed_', '')
                crop = FarmCrop.query.get(crop_code)
                inv_data["seeds"].append({
                    "item_code": item.item_code,
                    "crop_code": crop_code,
                    "name": crop.name if crop else crop_code,
                    "rarity": crop.rarity if crop else "COMMON",
                    "cefr_level": crop.cefr_level if crop else "A1",
                    "quantity": item.quantity,
                    "growth_seconds": crop.growth_seconds if crop else 60,
                    "pixel_art_svg": get_crop_svg(crop_code, 'mature', size=48)
                })
            else:
                shop_item = next((it for it in FARM_SHOP_ITEMS if it["code"] == item.item_code), None)
                inv_data["boosters"].append({
                    "item_code": item.item_code,
                    "name": shop_item["name"] if shop_item else item.item_code,
                    "effect_desc": shop_item["effect_desc"] if shop_item else "",
                    "icon_badge": shop_item["icon_badge"] if shop_item else "⚡",
                    "quantity": item.quantity
                })

    return jsonify({
        "status": "success",
        "user_coins": user.coins,
        "academic_rp": user.academic_rp,
        "plots": plots_data,
        "animals": get_animals_state_for_user(user_id),
        "inventory": inv_data,
        "server_time": datetime.now().isoformat()
    }), 200


@farm_bp.route('/crops', methods=['GET'])
def get_all_crops():
    """Lấy danh mục 20 loại cây trồng kèm SVG Pixel Art"""
    crops = FarmCrop.query.all()
    if not crops:
        user_id = session.get('user_id', 1)
        ensure_farm_initialized(user_id)
        crops = FarmCrop.query.all()

    crops_list = []
    for c in crops:
        cd = c.to_dict()
        cd["pixel_art_mature"] = get_crop_svg(c.code, 'mature', size=64)
        cd["pixel_art_sprout"] = get_crop_svg(c.code, 'sprout', size=64)
        cd["pixel_art_seed"] = get_crop_svg(c.code, 'seed', size=64)
        crops_list.append(cd)

    return jsonify({
        "status": "success",
        "total_crops": len(crops_list),
        "crops": crops_list
    }), 200


@farm_bp.route('/shop', methods=['GET'])
def get_farm_shop():
    """Lấy danh mục hàng hóa trong Cửa Hàng Nông Trại: Hạt giống 20 cây & 5 vật phẩm tăng tốc"""
    user_id = session.get('user_id')
    user_coins = 0
    if user_id:
        user = User.query.get(user_id)
        if user:
            user_coins = user.coins

    crops = FarmCrop.query.order_by(FarmCrop.seed_price).all()
    seeds_for_sale = []
    for c in crops:
        seeds_for_sale.append({
            "item_code": f"seed_{c.code}",
            "crop_code": c.code,
            "name": f"Hạt Giống {c.name}",
            "name_en": f"{c.name_en} Seeds",
            "rarity": c.rarity,
            "cefr_level": c.cefr_level,
            "price": c.seed_price,
            "harvest_coins": c.harvest_coins,
            "growth_seconds": c.growth_seconds,
            "description": c.description,
            "pixel_art_svg": get_crop_svg(c.code, 'mature', size=48)
        })

    return jsonify({
        "status": "success",
        "user_coins": user_coins,
        "boosters": FARM_SHOP_ITEMS,
        "seeds": seeds_for_sale
    }), 200


@farm_bp.route('/buy', methods=['POST'])
def buy_farm_item():
    """Mua hạt giống hoặc vật phẩm tăng tốc bằng Xu"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

    data = request.get_json() or {}
    item_code = data.get('item_code')
    quantity = max(1, int(data.get('quantity', 1)))

    if not item_code:
        return jsonify({"error": "Thiếu mã vật phẩm cần mua!"}), 400

    unit_price = 0
    item_type = 'BOOSTER'

    # Kiểm tra xem là Hạt giống hay Vật phẩm
    if item_code.startswith('seed_'):
        crop_code = item_code.replace('seed_', '')
        crop = FarmCrop.query.get(crop_code)
        if not crop:
            return jsonify({"error": "Hạt giống không tồn tại!"}), 404
        unit_price = crop.seed_price
        item_type = 'SEED'
    else:
        shop_item = next((it for it in FARM_SHOP_ITEMS if it["code"] == item_code), None)
        if not shop_item:
            return jsonify({"error": "Vật phẩm không tồn tại trong Shop!"}), 404
        unit_price = shop_item["price"]
        item_type = shop_item["type"]

    total_cost = unit_price * quantity
    if user.coins < total_cost:
        return jsonify({"error": f"Không đủ Xu! Cần {total_cost} Xu nhưng bạn chỉ có {user.coins} Xu."}), 400

    # Trừ Xu
    user.coins -= total_cost

    # Thêm vào kho
    inv_item = FarmInventory.query.filter_by(user_id=user_id, item_code=item_code).first()
    if not inv_item:
        inv_item = FarmInventory(user_id=user_id, item_type=item_type, item_code=item_code, quantity=quantity)
        db.session.add(inv_item)
    else:
        inv_item.quantity += quantity

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Mua thành công {quantity}x vật phẩm! Còn lại {user.coins} Xu.",
        "user_coins": user.coins,
        "item_code": item_code,
        "quantity": inv_item.quantity
    }), 200


@farm_bp.route('/plant', methods=['POST'])
def plant_crop():
    """Gieo hạt giống vào ô đất đã chọn"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json() or {}
    plot_id = data.get('plot_id')
    crop_code = data.get('crop_code')

    if not plot_id or not crop_code:
        return jsonify({"error": "Thiếu mã ô đất hoặc mã cây trồng!"}), 400

    plot = FarmPlot.query.filter_by(id=plot_id, user_id=user_id).first()
    if not plot:
        return jsonify({"error": "Ô đất không tồn tại hoặc không thuộc sở hữu của bạn!"}), 404
    if not plot.is_unlocked:
        return jsonify({"error": "Ô đất này chưa được mở khóa!"}), 400
    if plot.crop_code:
        return jsonify({"error": "Ô đất này đang có cây trồng, hãy đợi thu hoạch!"}), 400

    crop = FarmCrop.query.get(crop_code)
    if not crop:
        return jsonify({"error": "Loại cây trồng không hợp lệ!"}), 404

    # Kiểm tra hạt giống trong kho
    seed_item_code = f"seed_{crop_code}"
    inv_item = FarmInventory.query.filter_by(user_id=user_id, item_code=seed_item_code).first()
    if not inv_item or inv_item.quantity <= 0:
        return jsonify({"error": f"Bạn không có hạt giống {crop.name} trong kho! Hãy vào Shop để mua."}), 400

    # Trừ hạt giống
    inv_item.quantity -= 1

    now = datetime.now()
    plot.crop_code = crop_code
    plot.planted_at = now
    plot.harvest_ready_at = now + timedelta(seconds=crop.growth_seconds)
    plot.watered_count = 0
    plot.is_golden = False

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Đã gieo thành công hạt giống {crop.name} vào ô số {plot.plot_index + 1}!",
        "plot": plot.to_dict(),
        "remaining_seed_count": inv_item.quantity
    }), 200


@farm_bp.route('/water', methods=['POST'])
def water_plot():
    """Tưới nước cho ô đất đang trồng (Giảm 15% thời gian còn lại)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json() or {}
    plot_id = data.get('plot_id')
    plot = FarmPlot.query.filter_by(id=plot_id, user_id=user_id).first()
    if not plot or not plot.crop_code or not plot.harvest_ready_at:
        return jsonify({"error": "Ô đất chưa được gieo hạt!"}), 400

    now = datetime.now()
    if now >= plot.harvest_ready_at:
        return jsonify({"error": "Cây đã chín hoàn toàn, hãy thu hoạch ngay!"}), 400

    if plot.watered_count >= 1:
        return jsonify({"error": "Ô đất này đã được tưới nước trong chu kỳ này rồi!"}), 400

    # Giảm 15% thời gian còn lại
    remaining_sec = (plot.harvest_ready_at - now).total_seconds()
    reduction = remaining_sec * 0.15
    plot.harvest_ready_at = plot.harvest_ready_at - timedelta(seconds=reduction)
    plot.watered_count += 1

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Tưới nước mát lành! Giảm bớt {int(reduction)} giây thời gian sinh trưởng.",
        "plot": plot.to_dict()
    }), 200


@farm_bp.route('/apply-item', methods=['POST'])
def apply_booster_item():
    """Sử dụng phân bón hoặc thuốc tăng tốc để rút ngắn thời gian sinh trưởng"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    data = request.get_json() or {}
    plot_id = data.get('plot_id')
    item_code = data.get('item_code')

    plot = FarmPlot.query.filter_by(id=plot_id, user_id=user_id).first()
    if not plot or not plot.crop_code or not plot.harvest_ready_at:
        return jsonify({"error": "Ô đất chưa có cây trồng để bón phân!"}), 400

    now = datetime.now()
    if now >= plot.harvest_ready_at:
        return jsonify({"error": "Cây đã chín sẵn sàng thu hoạch, không cần dùng vật phẩm nữa!"}), 400

    inv_item = FarmInventory.query.filter_by(user_id=user_id, item_code=item_code).first()
    if not inv_item or inv_item.quantity <= 0:
        return jsonify({"error": "Bạn không có vật phẩm này trong kho!"}), 400

    # Áp dụng hiệu ứng
    remaining_sec = (plot.harvest_ready_at - now).total_seconds()
    msg = ""

    if item_code == 'fert_speed_25':
        reduction = remaining_sec * 0.25
        plot.harvest_ready_at = plot.harvest_ready_at - timedelta(seconds=reduction)
        msg = f"Đã bón Phân Hữu Cơ: Giảm {int(reduction)} giây!"
    elif item_code == 'fert_speed_50':
        reduction = remaining_sec * 0.50
        plot.harvest_ready_at = plot.harvest_ready_at - timedelta(seconds=reduction)
        msg = f"Đã bón Phân Tăng Tốc Turbo: Giảm {int(reduction)} giây!"
    elif item_code == 'fert_speed_75':
        reduction = remaining_sec * 0.75
        plot.harvest_ready_at = plot.harvest_ready_at - timedelta(seconds=reduction)
        msg = f"Đã tưới Tinh Chất Hyper: Rút ngắn thần tốc {int(reduction)} giây!"
    elif item_code == 'magic_water_instant':
        plot.harvest_ready_at = now - timedelta(seconds=5)
        msg = "Phép thuật Suối Thần! Cây trồng đã chín rực rỡ NGAY LẬP TỨC 100%!"
    elif item_code == 'fert_golden_double':
        reduction = remaining_sec * 0.50
        plot.harvest_ready_at = plot.harvest_ready_at - timedelta(seconds=reduction)
        plot.is_golden = True
        msg = f"Phân Bón Hoàng Kim! Giảm {int(reduction)}s và NHÂN ĐÔI phần thưởng Từ Vựng & Xu khi thu hoạch!"
    else:
        return jsonify({"error": "Vật phẩm không áp dụng được cho cây trồng!"}), 400

    inv_item.quantity -= 1
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": msg,
        "plot": plot.to_dict(),
        "remaining_item_count": inv_item.quantity
    }), 200


@farm_bp.route('/harvest', methods=['POST'])
def harvest_crop():
    """
    Thu hoạch cây trồng khi chín:
    1. Cộng Xu và Academic RP cho người chơi (x2 nếu có Phân Hoàng Kim).
    2. Rút ngẫu nhiên từ vựng mới theo đúng chuẩn CEFR từ ngân hàng 901 từ trong database.
    3. Mở khóa vào user_vocabularies để người chơi luyện tập bằng Spaced Repetition SRS.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

    data = request.get_json() or {}
    plot_id = data.get('plot_id')

    plot = FarmPlot.query.filter_by(id=plot_id, user_id=user_id).first()
    if not plot or not plot.crop_code:
        return jsonify({"error": "Ô đất trống, không có gì để thu hoạch!"}), 400

    now = datetime.now()
    if not plot.harvest_ready_at or now < plot.harvest_ready_at:
        remaining = int((plot.harvest_ready_at - now).total_seconds()) if plot.harvest_ready_at else 0
        return jsonify({"error": f"Cây chưa chín! Còn {remaining} giây nữa mới thu hoạch được."}), 400

    crop = FarmCrop.query.get(plot.crop_code)
    if not crop:
        return jsonify({"error": "Thông tin cây trồng bị lỗi!"}), 500

    # 1. Tính toán Xu & RP thưởng
    coin_multiplier = 2 if plot.is_golden else 1
    coins_awarded = crop.harvest_coins * coin_multiplier
    rp_awarded = crop.harvest_rp * coin_multiplier
    user.coins += coins_awarded
    user.academic_rp = (user.academic_rp or 500) + rp_awarded

    # 2. Rút từ vựng mới chuẩn CEFR theo cấp độ của cây
    vocab_multiplier = 2 if plot.is_golden else 1
    total_words_to_unlock = crop.vocab_count * vocab_multiplier

    # Tìm các từ vựng thuộc CEFR level tương ứng
    target_cefr = crop.cefr_level
    candidate_vocabs = Vocabulary.query.filter_by(cefr_level=target_cefr).all()
    if not candidate_vocabs:
        # Dự phòng nếu không có đúng level
        candidate_vocabs = Vocabulary.query.all()

    # Lấy danh sách ID từ vựng người dùng đã mở khóa
    user_vocab_ids = {
        uv.vocab_id for uv in UserVocabulary.query.filter_by(user_id=user_id, is_unlocked=True).all()
    }

    # Ưu tiên các từ người dùng chưa mở khóa
    unlocked_candidates = [v for v in candidate_vocabs if v.id not in user_vocab_ids]
    if not unlocked_candidates:
        unlocked_candidates = candidate_vocabs

    # Chọn ngẫu nhiên số từ tương ứng
    selected_vocabs = random.sample(unlocked_candidates, min(total_words_to_unlock, len(unlocked_candidates)))
    unlocked_words_info = []

    for v in selected_vocabs:
        uv = UserVocabulary.query.filter_by(user_id=user_id, vocab_id=v.id).first()
        if not uv:
            uv = UserVocabulary(
                user_id=user_id,
                vocab_id=v.id,
                is_unlocked=True,
                memorization_level='CHUA_THUOC',
                next_review_time=datetime.now()
            )
            db.session.add(uv)
        else:
            uv.is_unlocked = True

        unlocked_words_info.append({
            "id": v.id,
            "word": v.word,
            "meaning": v.meaning,
            "cefr_level": v.cefr_level,
            "theme": v.theme or "General"
        })

    # 3. Thu dọn ô đất về trạng thái trống
    harvested_crop_name = crop.name
    harvested_crop_rarity = crop.rarity
    plot.crop_code = None
    plot.planted_at = None
    plot.harvest_ready_at = None
    plot.watered_count = 0
    plot.is_golden = False

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Thu hoạch thành công {harvested_crop_name}! +{coins_awarded} Xu, +{rp_awarded} RP!",
        "crop_name": harvested_crop_name,
        "crop_rarity": harvested_crop_rarity,
        "coins_awarded": coins_awarded,
        "rp_awarded": rp_awarded,
        "user_coins": user.coins,
        "academic_rp": user.academic_rp,
        "unlocked_vocabularies": unlocked_words_info,
        "plot": plot.to_dict()
    }), 200


@farm_bp.route('/unlock-plot', methods=['POST'])
def unlock_plot():
    """Mở khóa ô đất mới bằng Xu"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Yêu cầu đăng nhập!"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng!"}), 404

    data = request.get_json() or {}
    plot_id = data.get('plot_id')

    plot = FarmPlot.query.filter_by(id=plot_id, user_id=user_id).first()
    if not plot:
        return jsonify({"error": "Ô đất không tồn tại!"}), 404
    if plot.is_unlocked:
        return jsonify({"error": "Ô đất này đã được mở khóa rồi!"}), 400

    cost = plot.unlock_cost or 50
    if user.coins < cost:
        return jsonify({"error": f"Không đủ Xu! Cần {cost} Xu để khai hoang ô đất này (Bạn có {user.coins} Xu)."}), 400

    user.coins -= cost
    plot.is_unlocked = True
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Khai hoang thành công ô đất số {plot.plot_index + 1}! Sẵn sàng gieo hạt.",
        "user_coins": user.coins,
        "plot": plot.to_dict()
    }), 200


@farm_bp.route('/interact-animal', methods=['POST'])
def interact_animal():
    """Tương tác gia súc (Bò, Gà, Heo) để nhận Xu & RP có Cooldown nghiêm ngặt"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "guest", "message": "Yêu cầu đăng nhập!"}), 200

    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "guest", "message": "Không tìm thấy người dùng!"}), 200

    data = request.get_json() or {}
    animal = data.get('animal', 'cow')
    if animal not in ANIMAL_CONFIGS:
        animal = 'cow'

    cfg = ANIMAL_CONFIGS[animal]
    now = datetime.now()
    last_time = _ANIMAL_LAST_INTERACTIONS.get((user_id, animal))

    if last_time:
        elapsed = (now - last_time).total_seconds()
        remaining = max(0, int(cfg["cooldown_seconds"] - elapsed))
        if remaining > 0:
            return jsonify({
                "status": "cooldown",
                "animal": animal,
                "name": cfg["name"],
                "remaining_seconds": remaining,
                "message": f"⏳ {cfg['name']} đang nghỉ ngơi! Vui lòng quay lại sau {remaining} giây nữa."
            }), 200

    # Đã hết cooldown -> Trao thưởng Xu và Điểm Academic RP
    _ANIMAL_LAST_INTERACTIONS[(user_id, animal)] = now
    reward_coins = cfg["reward_coins"]
    reward_rp = cfg["reward_rp"]

    user.coins = (user.coins or 0) + reward_coins
    user.academic_rp = (user.academic_rp or 0) + reward_rp
    db.session.commit()

    return jsonify({
        "status": "success",
        "animal": animal,
        "name": cfg["name"],
        "message": cfg["ready_msg"],
        "coins_reward": reward_coins,
        "rp_reward": reward_rp,
        "user_coins": user.coins,
        "academic_rp": user.academic_rp,
        "cooldown_seconds": cfg["cooldown_seconds"],
        "animals": get_animals_state_for_user(user_id)
    }), 200

