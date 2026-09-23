"""
PIXEL ART CROP & FARM GRAPHICS ENGINE (100% PURE SVG PIXEL MATRIX)
Tuyệt đối không dùng emoji hay icon thường.
Sử dụng lưới điểm ảnh SVG vector sắc nét crispEdges chuẩn phong cách Retro 16-bit.
"""

def generate_pixel_svg(grid: list, palette: dict, size: int = 64) -> str:
    """
    Sinh mã SVG từ ma trận điểm ảnh (grid ký tự) và bảng màu (palette).
    Mỗi ký tự trong grid tương ứng với một màu trong palette. '.' là trong suốt.
    """
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    rects = []

    for y, row in enumerate(grid):
        for x, char in enumerate(row):
            if char in palette and palette[char] is not None:
                color = palette[char]
                rects.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{color}"/>')

    svg_content = "".join(rects)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{size}" height="{size}" shape-rendering="crispEdges" class="pixel-art-svg">'
        f'{svg_content}</svg>'
    )


# -------------------------------------------------------------
# 1. GIAI ĐOẠN ĐẤT & MẦM CÂY DÙNG CHUNG
# -------------------------------------------------------------

# Ô đất xới khô
SOIL_EMPTY_GRID = [
    "................",
    "....########....",
    "..##88888888##..",
    ".#886688886688#.",
    "#88666688666688#",
    "#86666666666668#",
    "#88666688666688#",
    "#88888888888888#",
    ".#888888888888#.",
    "..##88888888##..",
    "....########....",
    "................"
]
SOIL_EMPTY_PALETTE = {
    '#': '#382212',
    '8': '#5a381e',
    '6': '#784d28'
}

# Ô đất tưới nước (ẩm ướt mỡ màu)
SOIL_WATERED_PALETTE = {
    '#': '#1b0f07',
    '8': '#2e1c0d',
    '6': '#422813',
    'w': '#38bdf8'
}

# Giai đoạn 1: Hạt mầm trong đất (Seed)
SEED_GRID = [
    "................",
    "................",
    "................",
    "......####......",
    ".....#YY88#.....",
    "....#YY8888#....",
    "....#Y88888#....",
    ".....#8888#.....",
    "......####......",
    ".......##.......",
    "....########....",
    "..##88888888##..",
    ".#886688886688#.",
    "#88666688666688#",
    "................",
    "................"
]
SEED_PALETTE = {
    '#': '#2e1c0d',
    'Y': '#fde047',
    '8': '#854d0e',
    '6': '#784d28'
}

# Giai đoạn 2: Mầm non 2 lá vươn lên (Sprout)
SPROUT_GRID = [
    "................",
    "....##....##....",
    "..#GG##..##GG#..",
    ".#GGgg####ggGG#.",
    ".#Ggggg##ggggG#.",
    "..#GggggggggG#..",
    "...##gggggg##...",
    ".....#gggg#.....",
    "......#GG#......",
    "......#GG#......",
    "......#88#......",
    "....######......",
    "..##888888##....",
    ".#8866888866##..",
    "#8866668866668#.",
    "................"
]
SPROUT_PALETTE = {
    '#': '#14532d',
    'G': '#4ade80',
    'g': '#22c55e',
    '8': '#5a381e',
    '6': '#784d28'
}


# -------------------------------------------------------------
# 2. TOÀN BỘ 20 LOẠI CÂY TRỒNG TRƯỞNG THÀNH (MATURE CROPS)
# -------------------------------------------------------------

CROPS_PIXEL_DATA = {
    # 1. CỦ CẢI KHỞI ĐẦU (Radish of Dawn - Common A1)
    "crop_radish": {
        "grid": [
            "......##..##....",
            ".....#GG##GG#...",
            "....#GggGGggG#..",
            ".....#ggGGgg#...",
            "......#GggG#....",
            ".....##RRRR##...",
            "....#RRrrRRrr#..",
            "...#RRrrrrrrRR#.",
            "...#RRrrrrrrRR#.",
            "...#RRrrrrrrRR#.",
            "....#RRrrrrRR#..",
            ".....##RRRR##...",
            ".......#WW#.....",
            "........#W#.....",
            ".........#......",
            "................"
        ],
        "palette": {
            '#': '#450a0a',
            'G': '#22c55e',
            'g': '#86efac',
            'R': '#e11d48',
            'r': '#fb7185',
            'W': '#ffffff'
        }
    },

    # 2. CÀ RỐT TINH ANH (Insight Carrot - Common A1)
    "crop_carrot": {
        "grid": [
            "....##..##..##..",
            "...#GG##GG##GG#.",
            "....#GggggggG#..",
            ".....##GggG##...",
            "......#GggG#....",
            ".....#OOOOOO#...",
            "....#OOooooOO#..",
            "....#OOooooOO#..",
            ".....#OOooOO#...",
            ".....#OOooOO#...",
            "......#OOooO#...",
            "......#OOooO#...",
            ".......#OOO#....",
            "........#OO#....",
            ".........#O#....",
            "..........#....."
        ],
        "palette": {
            '#': '#431407',
            'G': '#16a34a',
            'g': '#4ade80',
            'O': '#ea580c',
            'o': '#fb923c'
        }
    },

    # 3. KHOAI TÂY BỀN BỈ (Sturdy Potato - Common A1)
    "crop_potato": {
        "grid": [
            ".......####.....",
            "......#GGGG#....",
            ".....#GggggG#...",
            "......#GggG#....",
            "....##########..",
            "..##BBBBBBBBBB##",
            ".#BBbbBBbbBBbbB#",
            "#BBbbbbbbbbbbbbB",
            "#BBbbYYbbbbYYbbB",
            "#BBbbYYbbbbYYbbB",
            "#BBbbbbbbbbbbbbB",
            ".#BBbbBBbbBBbbB#",
            "..##BBBBBBBBBB##",
            "....##########..",
            "................",
            "................"
        ],
        "palette": {
            '#': '#27170a',
            'G': '#22c55e',
            'g': '#86efac',
            'B': '#78350f',
            'b': '#b45309',
            'Y': '#fde047'
        }
    },

    # 4. BẮP NGÔ NẮNG ẤM (Golden Sweetcorn - Common A1)
    "crop_corn": {
        "grid": [
            ".......####.....",
            "......#YYYY#....",
            ".....#YYyyYY#...",
            "....#YYyyyyYY#..",
            "...#G#YYyyYY#G#.",
            "..#GG#YYYYYY#GG#",
            ".#Ggg#YYyyYY#ggG",
            ".#Ggg#YYYYYY#ggG",
            ".#Ggg#YYyyYY#ggG",
            "..#Gg#YYYYYY#gG#",
            "...#G#YYyyYY#G#.",
            "....##YYYYYY##..",
            "......#GGGG#....",
            ".......#GG#.....",
            "........##......",
            "................"
        ],
        "palette": {
            '#': '#422006',
            'Y': '#eab308',
            'y': '#fef08a',
            'G': '#15803d',
            'g': '#4ade80'
        }
    },

    # 5. ĐẬU HÀ LAN TƯƠI (Fresh Pea Pod - Common A1)
    "crop_pea": {
        "grid": [
            "......##........",
            ".....#GG#.......",
            "....#GggG#......",
            "...#GggggG#.....",
            "..#GggggggG#....",
            ".#Gg##gg##gG#...",
            "#Gg#PP##PP#gG#..",
            "#G#PPPP##PPPPG#.",
            "#G#PPPP##PPPPG#.",
            ".#Gg#PP##PP#gG#.",
            "..#GggggggggG#..",
            "...#GggggggG#...",
            "....#GggggG#....",
            ".....#GggG#.....",
            "......#GG#......",
            ".......##......."
        ],
        "palette": {
            '#': '#052e16',
            'G': '#15803d',
            'g': '#22c55e',
            'P': '#a3e635'
        }
    },

    # 6. CÀ CHUA MỌNG NƯỚC (Ruby Tomato - Uncommon A2)
    "crop_tomato": {
        "grid": [
            ".....##..##.....",
            "....#GG##GG#....",
            ".....#GggG#.....",
            "....##########..",
            "..##RRRRRRRRRR##",
            ".#RRrrrrrrrrrrRR",
            "#RRrrWWrrrrrrrrR",
            "#RRrrWWrrrrrrrrR",
            "#RRrrrrrrrrrrrrR",
            "#RRrrrrrrrrrrrrR",
            ".#RRrrrrrrrrrrRR",
            "..##RRRRRRRRRR##",
            "....##########..",
            "................",
            "................",
            "................"
        ],
        "palette": {
            '#': '#450a0a',
            'G': '#15803d',
            'g': '#4ade80',
            'R': '#dc2626',
            'r': '#f87171',
            'W': '#ffffff'
        }
    },

    # 7. HÀNH TÂY CÚ PHÁP (Layered Onion - Uncommon A2)
    "crop_onion": {
        "grid": [
            ".......##.......",
            "......#GG#......",
            ".....#GggG#.....",
            "....#GggggG#....",
            ".....#GggG#.....",
            "....########....",
            "..##PPPPPPPP##..",
            ".#PPppppppppPP#.",
            "#PPppWWppppppPP#",
            "#PPppWWppppppPP#",
            "#PPppppppppppPP#",
            ".#PPppppppppPP#.",
            "..##PPPPPPPP##..",
            "....###WW###....",
            "......#WW#......",
            ".......##......."
        ],
        "palette": {
            '#': '#3b0764',
            'G': '#16a34a',
            'g': '#86efac',
            'P': '#7e22ce',
            'p': '#c084fc',
            'W': '#f5d0fe'
        }
    },

    # 8. DÂU TÂY NGỮ NGHĨA (Sweet Strawberry - Uncommon A2)
    "crop_strawberry": {
        "grid": [
            "....##..##..##..",
            "...#GG##GG##GG#.",
            "....#GggggggG#..",
            ".....##GggG##...",
            "...############.",
            "..#RRRRRRRRRRRR#",
            ".#RRrrYYrrrrYYr#",
            ".#RRrrrrrrrrrrr#",
            ".#RRrrYYrrrrYYr#",
            "..#RRrrrrrrrrr#.",
            "...#RRrrYYrrr#..",
            "....#RRrrrrr#...",
            ".....#RRrrr#....",
            "......#RRr#.....",
            ".......#R#......",
            "........#......."
        ],
        "palette": {
            '#': '#4c0519',
            'G': '#15803d',
            'g': '#4ade80',
            'R': '#e11d48',
            'r': '#fb7185',
            'Y': '#fde047'
        }
    },

    # 9. ỚT CHUÔNG RỰC LỬA (Blazing Bell Pepper - Uncommon A2)
    "crop_pepper": {
        "grid": [
            ".......####.....",
            "......#GGGG#....",
            ".......#GG#.....",
            ".....########...",
            "...##OOOOOOOO##.",
            "..#OOooooooooOO#",
            ".#OOooWWooooooOO",
            "#OOoooWWoooooooO",
            "#OOooooooooooooO",
            "#OOoo##oooo##ooO",
            "#OOo#OO#oo#OO#oO",
            ".#OO#OO#oo#OO#OO",
            "..##OOOOOOOO##..",
            "....########....",
            "................",
            "................"
        ],
        "palette": {
            '#': '#431407',
            'G': '#16a34a',
            'O': '#ea580c',
            'o': '#fb923c',
            'W': '#ffedd5'
        }
    },

    # 10. CÀ TÍM HUYỀN DIỆU (Mystic Eggplant - Uncommon A2)
    "crop_eggplant": {
        "grid": [
            ".....##..##.....",
            "....#GG##GG#....",
            ".....#GggG#.....",
            "....#GggggG#....",
            ".....######.....",
            "....#PPPPPP#....",
            "...#PPppppPP#...",
            "...#PPppWWppP#..",
            "...#PPppWWppP#..",
            "....#PPppppP#...",
            "....#PPppppP#...",
            ".....#PPppP#....",
            ".....#PPppP#....",
            "......#PPP#.....",
            ".......###......",
            "................"
        ],
        "palette": {
            '#': '#2e1065',
            'G': '#15803d',
            'g': '#4ade80',
            'P': '#581c87',
            'p': '#9333ea',
            'W': '#e9d5ff'
        }
    },

    # 11. HOA HƯỚNG DƯƠNG TRI THỨC (Scholar Sunflower - Rare B1)
    "crop_sunflower": {
        "grid": [
            "......#YYYY#....",
            "...#Y#YYYYYY#Y#.",
            "..#YYY#YYYY#YYY#",
            ".#YYYY######YYYY",
            "#YYYY#BBBBBB#YYY",
            "#YYY#BBbbbbBB#YY",
            "#YY#BBbbYYbbBB#Y",
            "#YY#BBbbYYbbBB#Y",
            "#YYY#BBbbbbBB#YY",
            "#YYYY#BBBBBB#YYY",
            ".#YYYY######YYYY",
            "..#YYY#YYYY#YYY#",
            "...#Y#GGGGGG#Y#.",
            "......#GGGG#....",
            ".......#GG#.....",
            "........##......"
        ],
        "palette": {
            '#': '#422006',
            'Y': '#facc15',
            'B': '#713f12',
            'b': '#a16207',
            'G': '#15803d'
        }
    },

    # 12. BÍ NGÔ HOÀNG KIM (Royal Pumpkin - Rare B1)
    "crop_pumpkin": {
        "grid": [
            ".......####.....",
            "......#GGGG#....",
            ".......#GG#.....",
            "....##########..",
            "..##OOOOOOOOOO##",
            ".#OOooOOooOOooOO",
            "#OOoooOOooOOoooO",
            "#OOoooOOooOOoooO",
            "#OOoooOOooOOoooO",
            "#OOoooOOooOOoooO",
            ".#OOooOOooOOooOO",
            "..##OOOOOOOOOO##",
            "....##########..",
            "................",
            "................",
            "................"
        ],
        "palette": {
            '#': '#451a03',
            'G': '#166534',
            'O': '#d97706',
            'o': '#fbbf24'
        }
    },

    # 13. NẤM DẠ QUANG OXFORD (Luminous Morel - Rare B1)
    "crop_mushroom": {
        "grid": [
            ".......####.....",
            ".....##CCCC##...",
            "....#CCccccCC#..",
            "...#CCccWWccCC#.",
            "..#CCccccccccCC#",
            ".#CCccWWccWWccCC",
            "#CCccccccccccccC",
            "################",
            ".....#WWWW#.....",
            "....#WWwwww#....",
            "....#WWwwww#....",
            "....#WWwwww#....",
            ".....#WWWW#.....",
            "....########....",
            "................",
            "................"
        ],
        "palette": {
            '#': '#082f49',
            'C': '#0284c7',
            'c': '#38bdf8',
            'W': '#f0f9ff',
            'w': '#bae6fd'
        }
    },

    # 14. CHÙM NHO THẠCH ANH (Amethyst Grape - Rare B1)
    "crop_grape": {
        "grid": [
            ".......####.....",
            "......#GGGG#....",
            "....##GggggG##..",
            "...#GGggggggGG#.",
            "....##########..",
            "....#PP#..#PP#..",
            "...#PppP##PppP#.",
            "...#PppP##PppP#.",
            "....#PP#PP#PP#..",
            "......#PppP#....",
            ".....#PPppPP#...",
            ".....#PppppP#...",
            "......#PppP#....",
            ".......#PP#.....",
            "........##......",
            "................"
        ],
        "palette": {
            '#': '#2e1065',
            'G': '#15803d',
            'g': '#86efac',
            'P': '#7c3aed',
            'p': '#c084fc'
        }
    },

    # 15. SEN NGỌC BÍCH TRI GIÁC (Jade Lotus - Epic B2)
    "crop_lotus": {
        "grid": [
            ".......####.....",
            "......#JJJJ#....",
            ".....#JJjjJJ#...",
            "....#JJjjjjJJ#..",
            "...#J#JJjjJJ#J#.",
            "..#JJ#JJjjJJ#JJ#",
            ".#JJjj######jjJJ",
            "#JJjj#YYyyYY#jjJ",
            "#JJjj#YyyyyY#jjJ",
            ".#JJj#YYyyYY#jJJ",
            "..##J########J##",
            "....#JJJJJJJJ#..",
            "...#GGGGGGGGGG#.",
            "..#GGggggggggGG#",
            "..##############",
            "................"
        ],
        "palette": {
            '#': '#064e3b',
            'J': '#059669',
            'j': '#34d399',
            'Y': '#fde047',
            'y': '#fef08a',
            'G': '#047857',
            'g': '#10b981'
        }
    },

    # 16. THANH LONG HỎA DIỆM (Dragon Pearl - Epic B2)
    "crop_dragon": {
        "grid": [
            "......##..##....",
            ".....#GG##GG#...",
            "....#GggGGggG#..",
            ".....#ggGGgg#...",
            "....##########..",
            "..##MMMMMMMMMM##",
            ".#MMmmGGmmGGmmMM",
            "#MMmmmmGGmmGGmmM",
            "#MMmmmmmmmmmmmmM",
            "#MMmmGGmmmmGGmmM",
            ".#MMmmGGmmGGmmMM",
            "..##MMMMMMMMMM##",
            "....#GG#..#GG#..",
            ".....##....##...",
            "................",
            "................"
        ],
        "palette": {
            '#': '#4a044e',
            'M': '#c026d3',
            'm': '#f472b6',
            'G': '#10b981',
            'g': '#6ee7b7'
        }
    },

    # 17. HOA PHA LÊ HÀN BĂNG (Frost Crystal Bloom - Epic B2)
    "crop_crystal": {
        "grid": [
            ".......####.....",
            "......#CCCC#....",
            ".....#CCccCC#...",
            "....#C#CccC#C#..",
            "...#CC#CccC#CC#.",
            "..#CCC######CCC#",
            ".#CCcc#WWWW#ccCC",
            "#CCccc#WWWW#cccC",
            "#CCccc#WWWW#cccC",
            ".#CCcc#WWWW#ccCC",
            "..#CCC######CCC#",
            "...#CC#CccC#CC#.",
            "....#C#CccC#C#..",
            ".....#CCccCC#...",
            "......#CCCC#....",
            ".......####....."
        ],
        "palette": {
            '#': '#0c4a6e',
            'C': '#0284c7',
            'c': '#38bdf8',
            'W': '#f0fdfa'
        }
    },

    # 18. NHÁNH CÂY THẾ GIỚI (Branch of Yggdrasil - Legendary C1)
    "crop_tree": {
        "grid": [
            ".....########...",
            "...##EEEEEEEE##.",
            "..#EEeeeeeeeeEE#",
            ".#EEeeGGeeGGeeEE",
            "#EEeeeGGeeGGeeeE",
            "#EEeeeeeeeeeeeeE",
            ".#EEee######eeEE",
            "..##EE#WWWW#EE##",
            "....###WWWW###..",
            "......#WWWW#....",
            ".....##WWWW##...",
            "....#WWWWWWWW#..",
            "...#WW##WW##WW#.",
            "..##W#..##..#W##",
            ".###..........##",
            "................"
        ],
        "palette": {
            '#': '#022c22',
            'E': '#047857',
            'e': '#10b981',
            'G': '#6ee7b7',
            'W': '#78350f'
        }
    },

    # 19. TÁO VÀNG VÔ TẬN (Infinity Golden Apple - Legendary C1/C2)
    "crop_apple": {
        "grid": [
            ".......####.....",
            "......#SSSS#....",
            ".......#SS#.....",
            "....##########..",
            "..##YYYYYYYYYY##",
            ".#YYyyYYyyYYyyYY",
            "#YYyyWWyyyyyyyYY",
            "#YYyyWWyyyyyyyYY",
            "#YYyyyyyyyyyyyYY",
            "#YYyyyyyyyyyyyYY",
            ".#YYyyYYyyYYyyYY",
            "..##YYYYYYYYYY##",
            "....##########..",
            ".......####.....",
            "................",
            "................"
        ],
        "palette": {
            '#': '#713f12',
            'S': '#94a3b8',
            'Y': '#eab308',
            'y': '#fef08a',
            'W': '#ffffff'
        }
    },

    # 20. HOA HỒNG TINH VÂN C2 (Cosmic Nebula Rose - Legendary C2)
    "crop_nebula": {
        "grid": [
            ".......####.....",
            ".....##VVVV##...",
            "....#VVvvvvVV#..",
            "...#VVvvSSvvVV#.",
            "..#VVvvSSSSvvVV#",
            ".#VVvvSSCCSSvvVV",
            "#VVvvSSCCCCSSvvV",
            "#VVvvSSCCCCSSvvV",
            "#VVvvSSCCSSvvvvV",
            ".#VVvvSSSSvvvvVV",
            "..#VVvvSSvvvvVV#",
            "...#VVvvvvvvVV#.",
            "....#VVVVVVVV#..",
            ".....##GGGG##...",
            ".......#GG#.....",
            "........##......"
        ],
        "palette": {
            '#': '#311042',
            'V': '#701a75',
            'v': '#d946ef',
            'S': '#38bdf8',
            'C': '#f43f5e',
            'G': '#059669'
        }
    }
}


# -------------------------------------------------------------
# 3. BỘ SINH SVG CÂY TRỒNG 3D ISOMETRIC CHUẨN HAY DAY
# -------------------------------------------------------------

def get_3d_crop_body(crop_code: str) -> str:
    """Sinh mã SVG chi tiết hình thể 3D cho 20 loại cây trồng"""
    if crop_code == "crop_corn":
        return """
        <!-- Bắp Ngô Nắng Ấm 3D -->
        <path d="M 47,82 Q 48,50 49,18" stroke="#15803d" stroke-width="7" stroke-linecap="round"/>
        <path d="M 48,64 Q 18,58 10,72 Q 26,65 48,68" fill="#22c55e" stroke="#166534" stroke-width="1.5"/>
        <path d="M 50,58 Q 80,52 90,68 Q 74,60 50,63" fill="#16a34a" stroke="#166534" stroke-width="1.5"/>
        <path d="M 48,40 Q 22,32 14,46 Q 30,38 48,44" fill="#4ade80" stroke="#166534" stroke-width="1.5"/>
        <path d="M 50,36 Q 78,28 88,42 Q 70,36 50,40" fill="#22c55e" stroke="#166534" stroke-width="1.5"/>
        <!-- Bắp ngô 1 -->
        <g transform="rotate(-18 36 48)">
          <ellipse cx="36" cy="48" rx="8" ry="16" fill="#facc15" stroke="#ca8a04" stroke-width="1.5"/>
          <line x1="32" y1="36" x2="32" y2="60" stroke="#eab308" stroke-width="1.5" stroke-dasharray="2 2"/>
          <line x1="36" y1="34" x2="36" y2="62" stroke="#eab308" stroke-width="1.5" stroke-dasharray="2 2"/>
          <line x1="40" y1="36" x2="40" y2="60" stroke="#eab308" stroke-width="1.5" stroke-dasharray="2 2"/>
          <path d="M 36,32 Q 33,24 28,26 M 36,32 Q 39,22 43,25" stroke="#b45309" stroke-width="1.5"/>
          <path d="M 28,56 Q 31,44 33,39 Q 32,53 34,64 Z" fill="#86efac" stroke="#15803d" stroke-width="1"/>
          <path d="M 44,56 Q 41,44 39,39 Q 40,53 38,64 Z" fill="#4ade80" stroke="#15803d" stroke-width="1"/>
        </g>
        <!-- Bắp ngô 2 -->
        <g transform="rotate(14 62 52)">
          <ellipse cx="62" cy="52" rx="7.5" ry="15" fill="#fde047" stroke="#ca8a04" stroke-width="1.5"/>
          <line x1="59" y1="40" x2="59" y2="64" stroke="#eab308" stroke-width="1.5" stroke-dasharray="2 2"/>
          <line x1="62" y1="38" x2="62" y2="66" stroke="#eab308" stroke-width="1.5" stroke-dasharray="2 2"/>
          <line x1="65" y1="40" x2="65" y2="64" stroke="#eab308" stroke-width="1.5" stroke-dasharray="2 2"/>
          <path d="M 62,37 Q 64,28 69,30" stroke="#b45309" stroke-width="1.5"/>
          <path d="M 55,60 Q 57,48 59,43 Q 58,57 60,67 Z" fill="#86efac" stroke="#15803d" stroke-width="1"/>
        </g>
        """

    elif crop_code == "crop_carrot":
        return """
        <!-- Cà Rốt Tinh Anh 3D -->
        <!-- 3 Củ cà rốt trồi lên mặt đất -->
        <polygon points="26,56 38,53 32,80" fill="#f97316" stroke="#c2410c" stroke-width="1.5"/>
        <ellipse cx="32" cy="54" rx="6" ry="2.5" fill="#fb923c"/>
        <line x1="28" y1="62" x2="35" y2="61" stroke="#ea580c" stroke-width="1"/>
        <line x1="29" y1="70" x2="34" y2="69" stroke="#ea580c" stroke-width="1"/>

        <polygon points="44,50 60,48 52,83" fill="#ea580c" stroke="#9a3412" stroke-width="2"/>
        <ellipse cx="52" cy="49" rx="8" ry="3" fill="#fb923c"/>
        <line x1="47" y1="58" x2="57" y2="57" stroke="#c2410c" stroke-width="1.5"/>
        <line x1="48" y1="68" x2="55" y2="67" stroke="#c2410c" stroke-width="1.5"/>

        <polygon points="62,56 73,53 67,78" fill="#f97316" stroke="#c2410c" stroke-width="1.5"/>
        <ellipse cx="67" cy="54" rx="5.5" ry="2.5" fill="#fb923c"/>

        <!-- Tán lá lông vũ vươn cao -->
        <path d="M 32,52 Q 22,30 14,20 Q 24,28 32,48" fill="#4ade80" stroke="#15803d" stroke-width="1.5"/>
        <path d="M 32,52 Q 30,22 26,10 Q 34,20 33,48" fill="#22c55e" stroke="#15803d" stroke-width="1.5"/>
        <path d="M 52,47 Q 48,16 50,4 Q 55,18 53,44" fill="#4ade80" stroke="#15803d" stroke-width="2"/>
        <path d="M 52,47 Q 64,18 74,10 Q 66,24 54,44" fill="#22c55e" stroke="#15803d" stroke-width="2"/>
        <path d="M 67,52 Q 76,32 86,22 Q 78,32 68,48" fill="#16a34a" stroke="#15803d" stroke-width="1.5"/>
        """

    elif crop_code == "crop_tomato":
        return """
        <!-- Cà Chua Mọng Nước 3D -->
        <!-- Bụi cây lá xanh -->
        <ellipse cx="50" cy="54" rx="36" ry="25" fill="#16a34a" stroke="#14532d" stroke-width="2"/>
        <ellipse cx="36" cy="44" rx="22" ry="18" fill="#22c55e"/>
        <ellipse cx="64" cy="44" rx="22" ry="18" fill="#15803d"/>
        <ellipse cx="50" cy="34" rx="20" ry="16" fill="#4ade80"/>
        <!-- Trái cà chua 1 -->
        <circle cx="32" cy="62" r="12" fill="#ef4444" stroke="#991b1b" stroke-width="1.5"/>
        <circle cx="28" cy="58" r="3.5" fill="#ffffff" opacity="0.7"/>
        <polygon points="32,50 30,46 34,44 36,47 33,52" fill="#22c55e"/>
        <!-- Trái cà chua 2 -->
        <circle cx="66" cy="58" r="13" fill="#ef4444" stroke="#991b1b" stroke-width="1.5"/>
        <circle cx="62" cy="53" r="4" fill="#ffffff" opacity="0.7"/>
        <polygon points="66,45 64,41 68,39 70,42 67,47" fill="#22c55e"/>
        <!-- Trái cà chua 3 -->
        <circle cx="48" cy="44" r="10.5" fill="#dc2626" stroke="#991b1b" stroke-width="1.5"/>
        <circle cx="45" cy="41" r="2.8" fill="#ffffff" opacity="0.8"/>
        <polygon points="48,34 46,31 49,29 51,32 49,36" fill="#4ade80"/>
        """

    elif crop_code == "crop_pumpkin":
        return """
        <!-- Bí Ngô Hoàng Kim 3D -->
        <ellipse cx="50" cy="62" rx="34" ry="22" fill="#ea580c" stroke="#9a3412" stroke-width="2.5"/>
        <ellipse cx="50" cy="62" rx="24" ry="21" fill="#f97316"/>
        <ellipse cx="50" cy="62" rx="12" ry="20" fill="#fb923c"/>
        <path d="M 50,41 Q 34,51 34,62 Q 34,73 50,83" stroke="#9a3412" stroke-width="1.8" fill="none"/>
        <path d="M 50,41 Q 66,51 66,62 Q 66,73 50,83" stroke="#9a3412" stroke-width="1.8" fill="none"/>
        <!-- Cuống quả xoắn -->
        <path d="M 50,43 Q 47,31 54,24 Q 59,26 53,43 Z" fill="#78350f" stroke="#451a03" stroke-width="1.5"/>
        <path d="M 53,36 Q 64,30 62,23 Q 57,18 63,13" stroke="#16a34a" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        """

    elif crop_code == "crop_sunflower":
        return """
        <!-- Hoa Hướng Dương Tri Thức 3D -->
        <path d="M 50,82 L 50,38" stroke="#15803d" stroke-width="7" stroke-linecap="round"/>
        <path d="M 50,64 Q 28,58 20,70 Q 34,66 50,68" fill="#22c55e" stroke="#15803d" stroke-width="1.5"/>
        <path d="M 50,54 Q 72,48 82,60 Q 66,56 50,58" fill="#16a34a" stroke="#15803d" stroke-width="1.5"/>
        <!-- Cụm cánh hoa tròn tỏa nắng -->
        <g transform="translate(50 34)">
          <ellipse cx="0" cy="-24" rx="6" ry="13" fill="#fde047" stroke="#ca8a04" stroke-width="1"/>
          <ellipse cx="17" cy="-17" rx="6" ry="13" fill="#facc15" stroke="#ca8a04" stroke-width="1" transform="rotate(45 17 -17)"/>
          <ellipse cx="24" cy="0" rx="6" ry="13" fill="#fde047" stroke="#ca8a04" stroke-width="1" transform="rotate(90 24 0)"/>
          <ellipse cx="17" cy="17" rx="6" ry="13" fill="#facc15" stroke="#ca8a04" stroke-width="1" transform="rotate(135 17 17)"/>
          <ellipse cx="0" cy="24" rx="6" ry="13" fill="#fde047" stroke="#ca8a04" stroke-width="1" transform="rotate(180 0 24)"/>
          <ellipse cx="-17" cy="17" rx="6" ry="13" fill="#facc15" stroke="#ca8a04" stroke-width="1" transform="rotate(225 -17 17)"/>
          <ellipse cx="-24" cy="0" rx="6" ry="13" fill="#fde047" stroke="#ca8a04" stroke-width="1" transform="rotate(270 -24 0)"/>
          <ellipse cx="-17" cy="-17" rx="6" ry="13" fill="#facc15" stroke="#ca8a04" stroke-width="1" transform="rotate(315 -17 -17)"/>
          <!-- Nhụy hoa nâu hạt -->
          <circle cx="0" cy="0" r="15" fill="#78350f" stroke="#451a03" stroke-width="2"/>
          <circle cx="0" cy="0" r="10" fill="#451a03"/>
          <circle cx="-3" cy="-3" r="2.5" fill="#d97706"/>
          <circle cx="4" cy="2" r="2.5" fill="#d97706"/>
        </g>
        """

    elif crop_code == "crop_strawberry":
        return """
        <!-- Dâu Tây Ngữ Nghĩa 3D -->
        <ellipse cx="50" cy="62" rx="30" ry="19" fill="#15803d" stroke="#14532d" stroke-width="2"/>
        <ellipse cx="35" cy="54" rx="18" ry="15" fill="#22c55e"/>
        <ellipse cx="65" cy="54" rx="18" ry="15" fill="#16a34a"/>
        <!-- Dâu 1 -->
        <g transform="translate(34 62)">
          <path d="M -9,-6 C -12,4 -5,14 0,16 C 5,14 12,4 9,-6 Z" fill="#ef4444" stroke="#991b1b" stroke-width="1.5"/>
          <circle cx="-3" cy="0" r="0.9" fill="#fde047"/><circle cx="3" cy="3" r="0.9" fill="#fde047"/><circle cx="-1" cy="7" r="0.9" fill="#fde047"/>
          <polygon points="-7,-6 -2,-4 0,-7 2,-4 7,-6 0,-2" fill="#22c55e"/>
        </g>
        <!-- Dâu 2 -->
        <g transform="translate(62 59)">
          <path d="M -10,-7 C -13,5 -6,15 0,17 C 6,15 13,5 10,-7 Z" fill="#f43f5e" stroke="#9f1239" stroke-width="1.5"/>
          <circle cx="-3" cy="0" r="0.9" fill="#fde047"/><circle cx="3" cy="4" r="0.9" fill="#fde047"/><circle cx="0" cy="9" r="0.9" fill="#fde047"/>
          <polygon points="-8,-7 -3,-5 0,-8 3,-5 8,-7 0,-3" fill="#22c55e"/>
        </g>
        <!-- Dâu 3 -->
        <g transform="translate(48 46)">
          <path d="M -8,-5 C -10,3 -4,12 0,14 C 4,12 10,3 8,-5 Z" fill="#ef4444" stroke="#991b1b" stroke-width="1.5"/>
          <polygon points="-5,-5 -2,-3 0,-6 2,-3 5,-5 0,-1" fill="#4ade80"/>
        </g>
        """

    elif crop_code == "crop_radish":
        return """
        <!-- Củ Cải Đỏ Khởi Đầu 3D -->
        <ellipse cx="50" cy="62" rx="18" ry="16" fill="#ec4899" stroke="#9d174d" stroke-width="2.5"/>
        <ellipse cx="44" cy="57" rx="5" ry="4" fill="#fbcfe8" opacity="0.6"/>
        <path d="M 44,72 Q 50,86 52,88 Q 51,77 56,72 Z" fill="#fdf2f8" stroke="#fbcfe8" stroke-width="1"/>
        <!-- Lá xanh xòe rộng -->
        <path d="M 48,50 Q 30,30 18,28 Q 32,36 46,52" fill="#4ade80" stroke="#16a34a" stroke-width="2"/>
        <path d="M 50,48 Q 50,18 46,10 Q 56,22 53,48" fill="#22c55e" stroke="#15803d" stroke-width="2"/>
        <path d="M 52,50 Q 70,30 82,28 Q 68,36 54,52" fill="#16a34a" stroke="#15803d" stroke-width="2"/>
        """

    elif crop_code == "crop_potato":
        return """
        <!-- Khoai Tây Bền Bỉ 3D -->
        <ellipse cx="38" cy="69" rx="18" ry="12" fill="#b4743c" stroke="#5a3311" stroke-width="2"/>
        <ellipse cx="60" cy="66" rx="20" ry="14" fill="#a0602c" stroke="#5a3311" stroke-width="2"/>
        <circle cx="34" cy="67" r="1.8" fill="#5a3311"/><circle cx="42" cy="73" r="1.8" fill="#5a3311"/>
        <circle cx="58" cy="62" r="1.8" fill="#5a3311"/><circle cx="68" cy="68" r="1.8" fill="#5a3311"/>
        <path d="M 48,60 Q 40,40 34,34 Q 44,40 48,58" fill="#4ade80" stroke="#16a34a" stroke-width="2"/>
        <path d="M 50,58 Q 56,36 62,32 Q 58,44 52,56" fill="#22c55e" stroke="#16a34a" stroke-width="2"/>
        """

    elif crop_code == "crop_eggplant":
        return """
        <!-- Cà Tím Huyền Diệu 3D -->
        <g transform="rotate(-15 42 56)">
          <path d="M 38,36 C 28,50 28,70 40,78 C 52,84 56,72 52,54 C 48,42 45,36 38,36 Z" fill="#7e22ce" stroke="#3b0764" stroke-width="2.5"/>
          <ellipse cx="46" cy="64" rx="4" ry="10" fill="#c084fc" opacity="0.65"/>
          <polygon points="34,36 40,43 45,34 49,42 45,30" fill="#22c55e" stroke="#15803d" stroke-width="1.5"/>
          <path d="M 43,31 Q 48,20 54,23" stroke="#15803d" stroke-width="3" fill="none" stroke-linecap="round"/>
        </g>
        """

    elif crop_code == "crop_apple":
        return """
        <!-- Táo Vàng Vô Tận 3D (Legendary) -->
        <circle cx="50" cy="52" r="28" fill="rgba(251, 191, 36, 0.3)" filter="drop-shadow(0 0 10px #fde047)"/>
        <path d="M 50,32 C 38,30 26,42 28,58 C 30,74 44,82 50,82 C 56,82 70,74 72,58 C 74,42 62,30 50,32 Z" fill="#facc15" stroke="#ca8a04" stroke-width="2.5"/>
        <ellipse cx="40" cy="48" rx="6" ry="12" fill="#fef08a" opacity="0.8"/>
        <path d="M 50,34 Q 52,22 60,20" stroke="#78350f" stroke-width="3.5" fill="none" stroke-linecap="round"/>
        <ellipse cx="64" cy="24" rx="9" ry="4.5" fill="#22c55e" stroke="#15803d" stroke-width="1.5" transform="rotate(-20 64 24)"/>
        <!-- Ánh sáng tinh thể -->
        <circle cx="58" cy="62" r="2.5" fill="#ffffff"/>
        <circle cx="44" cy="70" r="1.8" fill="#ffffff"/>
        """

    elif crop_code == "crop_tree":
        return """
        <!-- Cây Thế Giới Yggdrasil 3D (Legendary) -->
        <path d="M 44,84 Q 40,65 46,48 Q 54,65 56,84 Z" fill="#78350f" stroke="#451a03" stroke-width="2.5"/>
        <line x1="46" y1="58" x2="35" y2="48" stroke="#78350f" stroke-width="3"/>
        <line x1="50" y1="54" x2="62" y2="44" stroke="#78350f" stroke-width="3"/>
        <!-- Tán cây ngọc bích -->
        <ellipse cx="50" cy="38" rx="36" ry="26" fill="#047857" stroke="#064e3b" stroke-width="2.5"/>
        <ellipse cx="34" cy="32" rx="22" ry="18" fill="#10b981"/>
        <ellipse cx="66" cy="32" rx="22" ry="18" fill="#059669"/>
        <ellipse cx="50" cy="22" rx="24" ry="18" fill="#34d399"/>
        <circle cx="34" cy="32" r="3.5" fill="#67e8f9" filter="drop-shadow(0 0 4px #67e8f9)"/>
        <circle cx="66" cy="32" r="3.5" fill="#67e8f9" filter="drop-shadow(0 0 4px #67e8f9)"/>
        <circle cx="50" cy="20" r="4" fill="#fde047" filter="drop-shadow(0 0 5px #fde047)"/>
        """

    elif crop_code == "crop_nebula":
        return """
        <!-- Hoa Hồng Tinh Vân 3D (C2 Legendary) -->
        <circle cx="50" cy="46" r="30" fill="rgba(192, 132, 252, 0.3)" filter="drop-shadow(0 0 12px #d946ef)"/>
        <path d="M 50,82 L 50,56" stroke="#0284c7" stroke-width="5" stroke-linecap="round"/>
        <ellipse cx="50" cy="46" rx="25" ry="23" fill="#701a75" stroke="#3b0764" stroke-width="2"/>
        <ellipse cx="50" cy="46" rx="18" ry="16" fill="#c026d3"/>
        <ellipse cx="50" cy="46" rx="11" ry="10" fill="#06b6d4"/>
        <circle cx="50" cy="46" r="4.5" fill="#fef08a"/>
        <circle cx="41" cy="38" r="2" fill="#fff"/><circle cx="59" cy="42" r="2" fill="#fff"/>
        """

    elif crop_code == "crop_grape":
        return """
        <!-- Nho Thạch Anh 3D -->
        <ellipse cx="50" cy="36" rx="24" ry="12" fill="#15803d" stroke="#14532d" stroke-width="1.5"/>
        <g fill="#9333ea" stroke="#581c87" stroke-width="1.8">
          <circle cx="40" cy="46" r="6.5"/><circle cx="51" cy="45" r="6.5"/><circle cx="60" cy="48" r="6"/>
          <circle cx="36" cy="54" r="6"/><circle cx="46" cy="54" r="6.5"/><circle cx="56" cy="56" r="6"/>
          <circle cx="43" cy="63" r="6"/><circle cx="52" cy="63" r="6"/>
          <circle cx="48" cy="72" r="5.5"/>
        </g>
        <circle cx="45" cy="52" r="1.5" fill="#e9d5ff"/>
        <circle cx="50" cy="61" r="1.5" fill="#e9d5ff"/>
        """

    elif crop_code == "crop_mushroom":
        return """
        <!-- Nấm Dạ Quang Oxford 3D -->
        <path d="M 44,82 Q 43,62 46,50 Q 54,62 56,82 Z" fill="#f1f5f9" stroke="#94a3b8" stroke-width="2"/>
        <!-- Mũ nấm dạ quang -->
        <path d="M 22,52 C 22,26 78,26 78,52 C 68,54 32,54 22,52 Z" fill="#0284c7" stroke="#0369a1" stroke-width="2.5" filter="drop-shadow(0 0 8px #38bdf8)"/>
        <ellipse cx="50" cy="50" rx="27" ry="6" fill="#38bdf8"/>
        <circle cx="34" cy="38" r="3.5" fill="#ffffff" opacity="0.9"/>
        <circle cx="50" cy="34" r="4" fill="#ffffff" opacity="0.9"/>
        <circle cx="64" cy="38" r="3" fill="#ffffff" opacity="0.9"/>
        """

    elif crop_code == "crop_dragon":
        return """
        <!-- Thanh Long Hỏa Diệm 3D -->
        <ellipse cx="50" cy="58" rx="22" ry="25" fill="#ec4899" stroke="#be185d" stroke-width="2.5"/>
        <!-- Vảy rồng xanh -->
        <polygon points="40,42 46,34 50,44" fill="#22c55e" stroke="#15803d" stroke-width="1.5"/>
        <polygon points="50,42 56,32 60,42" fill="#22c55e" stroke="#15803d" stroke-width="1.5"/>
        <polygon points="30,54 24,46 32,48" fill="#22c55e" stroke="#15803d" stroke-width="1.5"/>
        <polygon points="70,54 76,46 68,48" fill="#22c55e" stroke="#15803d" stroke-width="1.5"/>
        <polygon points="34,68 26,64 36,60" fill="#22c55e" stroke="#15803d" stroke-width="1.5"/>
        <polygon points="66,68 74,64 64,60" fill="#22c55e" stroke="#15803d" stroke-width="1.5"/>
        <ellipse cx="45" cy="54" rx="4" ry="8" fill="#fbcfe8" opacity="0.6"/>
        """

    elif crop_code == "crop_crystal":
        return """
        <!-- Hoa Pha Lê Hàn Băng 3D -->
        <g filter="drop-shadow(0 0 10px #38bdf8)">
          <polygon points="50,20 62,38 50,56 38,38" fill="#38bdf8" stroke="#0284c7" stroke-width="2"/>
          <polygon points="26,44 44,52 38,70 20,62" fill="#7dd3fc" stroke="#0284c7" stroke-width="1.8"/>
          <polygon points="74,44 56,52 62,70 80,62" fill="#0284c7" stroke="#0369a1" stroke-width="1.8"/>
          <polygon points="50,42 60,54 50,66 40,54" fill="#ffffff" opacity="0.85"/>
          <line x1="50" y1="66" x2="50" y2="82" stroke="#0369a1" stroke-width="4"/>
        </g>
        """

    elif crop_code == "crop_lotus":
        return """
        <!-- Sen Ngọc Bích 3D -->
        <ellipse cx="50" cy="74" rx="34" ry="12" fill="#059669" stroke="#064e3b" stroke-width="2"/>
        <!-- Cánh sen đa tầng -->
        <path d="M 50,30 C 40,45 32,60 50,70 C 68,60 60,45 50,30 Z" fill="#f472b6" stroke="#db2777" stroke-width="1.5"/>
        <path d="M 32,45 C 26,55 30,68 45,70 C 40,60 36,52 32,45 Z" fill="#fb7185" stroke="#e11d48" stroke-width="1.5"/>
        <path d="M 68,45 C 74,55 70,68 55,70 C 60,60 64,52 68,45 Z" fill="#fb7185" stroke="#e11d48" stroke-width="1.5"/>
        <circle cx="50" cy="58" r="6" fill="#fde047" stroke="#ca8a04" stroke-width="1"/>
        """

    elif crop_code == "crop_pepper":
        return """
        <!-- Ớt Chuông Rực Lửa 3D -->
        <g transform="rotate(-10 40 58)">
          <path d="M 32,42 C 26,48 26,72 40,76 C 50,74 52,66 48,52 C 46,42 42,42 32,42 Z" fill="#ef4444" stroke="#991b1b" stroke-width="2"/>
          <ellipse cx="44" cy="56" rx="3" ry="8" fill="#fca5a5" opacity="0.6"/>
          <path d="M 36,42 Q 38,30 46,32" stroke="#15803d" stroke-width="3" fill="none" stroke-linecap="round"/>
        </g>
        <g transform="rotate(12 60 60)">
          <path d="M 52,44 C 46,50 46,72 58,76 C 68,74 70,66 66,54 C 64,44 60,44 52,44 Z" fill="#facc15" stroke="#ca8a04" stroke-width="2"/>
          <ellipse cx="63" cy="58" rx="3" ry="8" fill="#fef08a" opacity="0.7"/>
          <path d="M 56,44 Q 58,32 64,34" stroke="#15803d" stroke-width="3" fill="none" stroke-linecap="round"/>
        </g>
        """

    elif crop_code == "crop_pea":
        return """
        <!-- Đậu Hà Lan Tươi 3D -->
        <path d="M 50,82 Q 44,56 46,30" stroke="#15803d" stroke-width="4" stroke-linecap="round"/>
        <!-- Pod 1 -->
        <g transform="rotate(-20 38 48)">
          <path d="M 24,42 Q 42,38 52,50 Q 38,58 24,42 Z" fill="#22c55e" stroke="#15803d" stroke-width="2"/>
          <circle cx="33" cy="46" r="3.5" fill="#86efac" stroke="#15803d" stroke-width="1"/>
          <circle cx="41" cy="48" r="3.5" fill="#86efac" stroke="#15803d" stroke-width="1"/>
          <circle cx="48" cy="51" r="3" fill="#86efac" stroke="#15803d" stroke-width="1"/>
        </g>
        <!-- Pod 2 -->
        <g transform="rotate(25 60 56)">
          <path d="M 48,50 Q 64,48 74,60 Q 62,68 48,50 Z" fill="#16a34a" stroke="#15803d" stroke-width="2"/>
          <circle cx="56" cy="54" r="3" fill="#4ade80"/>
          <circle cx="64" cy="57" r="3" fill="#4ade80"/>
        </g>
        """

    elif crop_code == "crop_onion":
        return """
        <!-- Hành Tây Cú Pháp 3D -->
        <ellipse cx="50" cy="64" rx="20" ry="18" fill="#c084fc" stroke="#581c87" stroke-width="2"/>
        <path d="M 50,46 Q 42,55 42,64 Q 42,73 50,82" stroke="#7e22ce" stroke-width="1.5" fill="none"/>
        <path d="M 50,46 Q 58,55 58,64 Q 58,73 50,82" stroke="#7e22ce" stroke-width="1.5" fill="none"/>
        <!-- Chồi lá xanh -->
        <path d="M 50,48 Q 44,28 36,20" stroke="#22c55e" stroke-width="3" stroke-linecap="round"/>
        <path d="M 50,48 Q 50,22 52,14" stroke="#4ade80" stroke-width="3" stroke-linecap="round"/>
        <path d="M 50,48 Q 56,28 64,22" stroke="#16a34a" stroke-width="3" stroke-linecap="round"/>
        """

    # Mặc định (generic 3D plant)
    return """
    <path d="M 50,80 L 50,40" stroke="#15803d" stroke-width="6" stroke-linecap="round"/>
    <ellipse cx="36" cy="46" rx="16" ry="10" fill="#22c55e" stroke="#15803d" stroke-width="1.5" transform="rotate(-30 36 46)"/>
    <ellipse cx="64" cy="46" rx="16" ry="10" fill="#16a34a" stroke="#15803d" stroke-width="1.5" transform="rotate(30 64 46)"/>
    <circle cx="50" cy="34" r="14" fill="#facc15" stroke="#ca8a04" stroke-width="2"/>
    """


def get_crop_svg(crop_code: str, stage: str = 'mature', size: int = 84) -> str:
    """
    Sinh SVG 3D Isometric chân thực và sống động chuẩn game nông trại Hay Day:
    - Có mô đất cày xới 3D & bóng đổ mềm mại dưới gốc.
    - Cây trồng có chiều sâu, góc nghiêng 2.5D, màu sắc phân tầng rực rỡ.
    """
    soil_mound = """
    <!-- 3D Isometric Soil Bed & Furrow Base -->
    <ellipse cx="50" cy="80" rx="36" ry="12" fill="#2b1506" opacity="0.6"/>
    <polygon points="14,80 50,92 86,80 50,68" fill="#5c2e0b" stroke="#3b1d06" stroke-width="2"/>
    <polygon points="20,77 50,87 80,77 50,67" fill="#753d10" opacity="0.75"/>
    """

    if stage == 'empty':
        body = """
        <!-- Luống đất trống cày xới mỡ màu -->
        <ellipse cx="50" cy="80" rx="20" ry="6" fill="#3a1c06"/>
        <circle cx="50" cy="76" r="3" fill="#10b981" opacity="0.75"/>
        """
    elif stage == 'seed':
        body = """
        <!-- Hạt mầm 3D nhú mầm non trong đất -->
        <ellipse cx="50" cy="78" rx="8" ry="5" fill="#facc15" stroke="#ca8a04" stroke-width="1.5"/>
        <path d="M 50,75 Q 48,64 52,58" stroke="#4ade80" stroke-width="3" stroke-linecap="round"/>
        <circle cx="53" cy="57" r="2.5" fill="#86efac"/>
        """
    elif stage == 'sprout':
        body = """
        <!-- Cây mầm 2 lá xanh non 3D -->
        <path d="M 50,80 Q 48,60 50,48" stroke="#16a34a" stroke-width="4.5" stroke-linecap="round"/>
        <path d="M 50,56 Q 32,46 25,54 Q 38,56 50,60" fill="#4ade80" stroke="#15803d" stroke-width="1.5"/>
        <path d="M 50,52 Q 68,42 75,50 Q 62,52 50,56" fill="#22c55e" stroke="#15803d" stroke-width="1.5"/>
        <circle cx="50" cy="46" r="3" fill="#86efac"/>
        """
    else:
        # Mature
        body = get_3d_crop_body(crop_code)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="{size}" height="{size}" class="iso-3d-crop-svg">
        {soil_mound}
        {body}
    </svg>"""

