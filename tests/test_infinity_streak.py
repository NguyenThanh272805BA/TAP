import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import json
from app import create_app, db
from app.models.user import User
from app.models.vocabulary import Vocabulary

app = create_app()
with app.app_context():
    # 1. Update thanh123 infinity_score to 10 if needed
    u = User.query.filter_by(username='thanh123').first()
    if u:
        if (u.infinity_score or 0) < 10:
            u.infinity_score = 10
            db.session.commit()
            print(f"Updated thanh123 infinity_score to {u.infinity_score}")
        else:
            print(f"thanh123 already has infinity_score = {u.infinity_score}")

    # 2. Test simulating 10 consecutive correct answers in client session
    client = app.test_client()
    
    # Login as thanh123
    with client.session_transaction() as sess:
        sess['user_id'] = u.id

    # Reset streak for test
    u.infinity_score = 0
    db.session.commit()

    # Roll and answer 10 questions
    import time
    streak = 0
    for i in range(1, 11):
        # Roll
        res_roll = client.post('/api/game/gacha/roll', json={'mode': 'infinity', 'current_streak': streak})
        data_roll = res_roll.get_json()
        assert res_roll.status_code == 200, f"Roll failed: {data_roll}"
        vocab_id = data_roll['vocab_id']
        vocab = Vocabulary.query.get(vocab_id)

        # Wait > 150ms to pass anti-cheat
        time.sleep(0.2)

        # Verify correct answer
        res_ver = client.post('/api/game/gacha/verify', json={
            'vocab_id': vocab_id,
            'answer': vocab.meaning,
            'mode': 'infinity',
            'current_streak': streak
        })
        data_ver = res_ver.get_json()
        assert res_ver.status_code == 200, f"Verify failed: {data_ver}"
        assert data_ver['is_correct'] is True
        assert data_ver['new_streak'] == i, f"Expected streak {i}, got {data_ver['new_streak']}"
        assert data_ver['infinity_score'] == i, f"Expected infinity_score {i}, got {data_ver['infinity_score']}"
        streak = data_ver['new_streak']
        print(f"Question {i}: Streak = {streak}, Best = {data_ver['infinity_score']}")

    # Check user in DB
    db.session.refresh(u)
    assert u.infinity_score == 10, f"Expected u.infinity_score == 10, got {u.infinity_score}"
    print("[PASS] 10 consecutive correct answers recorded infinity_score = 10!")

    # Check wrong answer / game over
    vocab = Vocabulary.query.first()
    res_fail = client.post('/api/game/gacha/verify', json={
        'vocab_id': vocab.id,
        'answer': 'WRONG_ANSWER_INTENTIONAL',
        'mode': 'infinity',
        'current_streak': streak
    })
    data_fail = res_fail.get_json()
    assert data_fail['is_correct'] is False
    assert data_fail['is_game_over'] is True
    assert data_fail['new_streak'] == 0
    assert "Dừng lại ở chuỗi: 10 combo!" in data_fail['message']
    print(f"[PASS] Game over message: {data_fail['message']}")

    # 3. Test /api/auth/user/me returns infinity_score and arena_stage
    res_me = client.get('/api/auth/user/me')
    data_me = res_me.get_json()
    assert data_me['infinity_score'] == 10
    assert 'arena_stage' in data_me
    print(f"[PASS] /api/auth/user/me: infinity_score={data_me['infinity_score']}, arena_stage={data_me['arena_stage']}")

    # 4. Test /api/leaderboard?category=game
    res_lb = client.get('/api/leaderboard?category=game')
    data_lb = res_lb.get_json()
    assert data_lb['status'] == 'success'
    assert data_lb['primary_metric'] == 'infinity_score'
    assert data_lb['unit'] == 'pts'
    
    # Find thanh123 in leaderboard
    my_rank = data_lb['my_rank']
    print(f"[PASS] Leaderboard my_rank: {my_rank['username']} Rank #{my_rank['rank']} with {my_rank['primary_value']} {my_rank['unit']}")
    assert my_rank['primary_value'] == 10

    print("ALL TESTS PASSED SUCCESSFULLY!")
