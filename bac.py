def _format_vcpr_message(all_reports) -> str:
    now_ist = datetime.now(IST)
    ts = now_ist.strftime("%d %b %Y %H:%M IST")

    header = "🌅 👻 <b>Virgin CPR Consolidated Alert</b>"

    lines = [
        header,
        f"🕐 {ts}",
        "════════════════════════════"
    ]

    total_count = 0

    for symbol, reports in all_reports.items():
        if not reports:
            continue

        total_count += len(reports)

        lines.append(
            f"\n🔹 <b>{symbol}</b> | "
            f"<b>VCPR Count:</b> {len(reports)}"
        )

        for report in reports:
            lines.append(
                f"   └─Date: {report[0]} | width: {report[3]:.1f}"
            )

    lines += [
        "",
        "════════════════════════════",
        f"📊 <b>Total Active VCPRs:</b> {total_count}",
        "",
        "📖 <b>Guide:</b>",
        "🔴 Wide CPR = strong magnet / bigger reaction",
        "🟢 Narrow CPR = breakout probability high",
        "⚡ Action = wait for reaction + confirmation candle"
    ]

    return "\n".join(lines)