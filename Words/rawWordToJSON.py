import os
import json
import random


def word_to_json(file_path="Words/words.txt", num_normal=10, num_hard=5, bonus_normal=1, bonus_hard=1):
    def filter_words(words, min_len, max_len):
        return [word for word in words if min_len <= len(word) <= max_len]

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Error: File '{file_path}' does not exist.")

    with open(file_path, 'r') as file:
        data = file.read()


    # Words per puzzle for each mode
    normal_w_count = 10
    hard_w_count = 15

    sections = data.split('====================')
    result = {}

    for section in sections:
        if section.strip():
            lines = section.strip().splitlines()
            topic = lines[0].strip('>').strip()
            words = [word.strip() for word in lines[1:] if word.strip()]

            # Prepare pools and ensure enough words
            normal_pool = filter_words(words, 4, 11)
            hard_pool = filter_words(words, 6, 15)

            # Required totals
            total_normal_needed = num_normal * normal_w_count
            total_hard_needed = num_hard * hard_w_count
            total_bonus_norm_needed = bonus_normal * normal_w_count
            total_bonus_hard_needed = bonus_hard * hard_w_count
            # Check availability
            if len(normal_pool) < total_normal_needed + total_bonus_norm_needed:
                raise ValueError(f"Topic '{topic}' needs {total_normal_needed + total_bonus_norm_needed} normal words, found {len(normal_pool)}")
            if len(hard_pool) < total_hard_needed + total_bonus_hard_needed:
                raise ValueError(f"Topic '{topic}' needs {total_hard_needed + total_bonus_hard_needed} hard words, found {len(hard_pool)}")

            topic_result = {"Normal": [], "Hard": [], "Bonus": {"Normal": [], "Hard": []}}
            # Sample unique words
            # Normal puzzles
            for _ in range(num_normal):
                sample = random.sample(normal_pool, normal_w_count)
                topic_result["Normal"].append(sample)
                for w in sample:
                    if w in normal_pool: normal_pool.remove(w)
                    #if w in hard_pool: hard_pool.remove(w)
            
            # Hard puzzles
            for _ in range(num_hard):
                sample = random.sample(hard_pool, hard_w_count)
                topic_result["Hard"].append(sample)
                for w in sample:
                    if w in hard_pool: hard_pool.remove(w)
                    #if w in normal_pool: normal_pool.remove(w)
            
            # Bonus Normal puzzles
            for _ in range(bonus_normal):
                sample = random.sample(normal_pool, normal_w_count)
                topic_result["Bonus"]["Normal"].append(sample)
                for w in sample:
                    normal_pool.remove(w)
                    #if w in hard_pool: hard_pool.remove(w)
            
            # Bonus Hard puzzles
            for _ in range(bonus_hard):
                sample = random.sample(hard_pool, hard_w_count)
                topic_result["Bonus"]["Hard"].append(sample)
                for w in sample:
                    hard_pool.remove(w)
                    #if w in normal_pool: normal_pool.remove(w)
            
            result[topic] = topic_result

    # Write JSON
    with open("Words/words.json", "w") as f:
        json.dump(result, f, indent=4)


if __name__ == '__main__':
    word_to_json("Words/words.txt", num_normal=10, num_hard=5, bonus_normal=1, bonus_hard=1)
