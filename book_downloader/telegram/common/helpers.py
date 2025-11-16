def itoa(i: int) -> str:
    alphabet = ('0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')
    if not i:
        return alphabet[0]

    result = ''
    while i:
        i, remainder = divmod(i, 10)
        result = alphabet[remainder] + result

    return result
