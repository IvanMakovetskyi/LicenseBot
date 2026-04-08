from database.db import getConection

def getCase(chatId: int):
    conn = getConection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cases WHERE chat_id = ?",
        (chatId,)
    )

    case = cursor.fetchone()
    conn.close()
    return case

def createCase(chatId: int, usState: str, status: str = "new"):
    conn = getConection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO cases (chat_id, us_state, status) VALUES (?, ?, ?)",
        (chatId, usState, status)
    )

    conn.commit()
    conn.close()
