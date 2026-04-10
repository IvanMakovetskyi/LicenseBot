from database.db import getConnection


def getCase(chatId: int):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cases WHERE chat_id = ?",
        (chatId,)
    )

    case = cursor.fetchone()
    conn.close()
    return case


def getCaseById(caseId: int):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cases WHERE id = ?",
        (caseId,)
    )

    case = cursor.fetchone()
    conn.close()
    return case


def getAllCases():
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cases ORDER BY id DESC"
    )

    cases = cursor.fetchall()
    conn.close()
    return cases


def createCase(chatId: int, fullName: str, usState: str, status: str = "new"):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO cases (chat_id, full_name, us_state, status) VALUES (?, ?, ?, ?)",
        (chatId, fullName, usState, status)
    )

    conn.commit()
    conn.close()


def deleteCase(caseId: int):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM cases WHERE id = ?",
        (caseId,)
    )

    conn.commit()
    conn.close()


def updateCaseStatus(caseId: int, status: str):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE cases SET status = ? WHERE id = ?",
        (status, caseId)
    )

    conn.commit()
    conn.close()
