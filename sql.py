import sqlite3


class Database():
    def __init__(self, database):
        self.con = sqlite3.connect(database)
        self.cur = self.con.cursor()

    # ******************_MAIN_******************
    def user_exists(self, user_id):
        with self.con:
            r = self.cur.execute('SELECT * FROM `users` WHERE `id` = ?', (user_id,)).fetchall()
            return bool(len(r))

    def add_user(self, user_id, username, name, tg_name, phone, ref, reg_date):
        with self.con:
            return self.cur.execute(
                'INSERT INTO `users` (`id`, `ref`, `name`, `tg_name`, `username`, `phone`, `date`)'
                'VALUES (?, ?, ?, ?, ?, ?, ?)', (user_id, ref, name, tg_name, username, phone, reg_date)
            )

    def get_group(self, user_id):
        with self.con:
            return self.cur.execute('SELECT `group` FROM `users` WHERE `id` = ?', (user_id,)).fetchone()[0]

    def get_phone(self, user_id):
        with self.con:
            return self.cur.execute('SELECT `phone` FROM `users` WHERE `id` = ?', (user_id,)).fetchone()[0]

    def get_id(self, user_id):
        with self.con:
            return self.cur.execute('SELECT `id` FROM `users` WHERE `id` = ?', (user_id,)).fetchone()[0]

    def get_tgname(self, user_id):
        with self.con:
            return self.cur.execute('SELECT `tg_name` FROM `users` WHERE `id` = ?', (user_id,)).fetchone()[0]

    def get_username(self, user_id):
        with self.con:
            return self.cur.execute('SELECT `username` FROM `users` WHERE `id` = ?', (user_id,)).fetchone()[0]

    def get_name(self, user_id):
        with self.con:
            return self.cur.execute('SELECT `name` FROM `users` WHERE `id` = ?', (user_id,)).fetchone()[0]

    def get_date(self, user_id):
        with self.con:
            return self.cur.execute('SELECT `date` FROM `users` WHERE `id` = ?', (user_id,)).fetchone()[0]

    def get_balance(self, user_id):
        with self.con:
            return self.cur.execute('SELECT `balance` FROM `users` WHERE `id` = ?', (user_id,)).fetchone()[0]

    def get_total_balance(self):
        with self.con:
            return self.cur.execute('SELECT SUM(`balance`) FROM `users`').fetchone()[0]

    def get_status(self, user_id):
        with self.con:
            return self.cur.execute('SELECT `status` FROM `users` WHERE `id` = ?', (user_id,)).fetchone()[0]

    def get_refs(self, user_id):
        with self.con:
            return self.cur.execute('SELECT `id` FROM `users` WHERE `ref` = ?', (user_id,)).fetchall()

    def get_all(self):
        with self.con:
            return self.cur.execute('SELECT `id` FROM `users`').fetchall()

    def get_all_agents(self):
        with self.con:
            return self.cur.execute('SELECT `id` FROM `users` WHERE `group` = 1').fetchall()

    def get_all_refs(self):
        with self.con:
            return self.cur.execute('SELECT `id` FROM `users` WHERE `group` = 0').fetchall()

    def get_comment(self, user_id):
        with self.con:
            return self.cur.execute('SELECT `comment` FROM `users` WHERE `id` = ?', (user_id,)).fetchone()[0]

    def get_ref(self, user_id):
        with self.con:
            return self.cur.execute('SELECT `ref` FROM `users` WHERE `id` = ?', (user_id,)).fetchone()[0]

    def user_exists_by_phone(self, phone_number):
        with self.con:
            result = self.cur.execute('SELECT COUNT(*) FROM `users` WHERE `phone` = ?', (phone_number,)).fetchone()
            return result[0] > 0

    def get_user_id_by_phone(self, phone_number):
        with self.con:
            result = self.cur.execute('SELECT `id` FROM `users` WHERE `phone` = ?', (phone_number,)).fetchone()
            return result[0] if result else None

    def add_to_balance(self, user_id, amount):
        with self.con:
            self.cur.execute('UPDATE `users` SET `balance` = `balance` + ? WHERE `id` = ?', (amount, user_id))

    def record_award(self, user_id, phone, award_type, award_amount):
        with self.con:
            self.cur.execute('INSERT INTO `awards` (`user_id`, `phone`, `type`, `amount`, `date`) VALUES (?, ?, ?, ?, datetime("now"))', (user_id, phone, award_type, award_amount))

    def get_reward_amount(self, award_type):
        with self.con:
            result = self.cur.execute('SELECT `amount` FROM `reward_types` WHERE `type` = ?', (award_type,)).fetchone()
            return result[0] if result else None

    def get_all_reward_types(self):
        with self.con:
            return self.cur.execute('SELECT type FROM reward_types').fetchall()

    def update_reward_amount(self, reward_type, new_amount):
        with self.con:
            self.cur.execute('UPDATE reward_types SET amount = ? WHERE type = ?', (new_amount, reward_type))
            return self.cur.rowcount > 0

    def set_comment(self, user_id, text):
        with self.con:
            return self.cur.execute('UPDATE `users` SET  `comment` = ? WHERE `id` = ?', (text, user_id,))

    def set_status(self, user_id, status):
        with self.con:
            return self.cur.execute('UPDATE `users` SET  `status` = ? WHERE `id` = ?', (status, user_id,))

    def set_group(self, user_id, status):
        with self.con:
            return self.cur.execute('UPDATE `users` SET  `group` = ? WHERE `id` = ?', (status, user_id,))


