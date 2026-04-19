def calculate_growth(data: list[float], period: int = 1):
    growth = []

    for i in range(len(data)):
        if i < period:
            growth.append(None)  # not enough data
            continue

        prev = data[i - period]

        if prev == 0:
            growth.append(None)
        else:
            value = ((data[i] - prev) / prev) * 100
            growth.append(round(value, 2))

    return growth