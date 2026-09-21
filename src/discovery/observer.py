def observe_page(page):

    observation = {
        "url": page.url,
        "title": page.title(),
        "text": page.locator("body").inner_text(),
        "controls": [],
        "data": []
    }

    control_number = 1
    data_number = 1

    # ==========================================
    # INPUT FIELDS
    # ==========================================

    inputs = page.locator("input")

    for i in range(inputs.count()):

        element = inputs.nth(i)

        element_id = element.get_attribute("id")
        name = element.get_attribute("name")
        input_type = element.get_attribute("type")
        placeholder = element.get_attribute(
            "placeholder"
        )

        label = None

        if element_id:

            label_locator = page.locator(
                f'label[for="{element_id}"]'
            )

            if label_locator.count() > 0:

                label = (
                    label_locator
                    .first
                    .inner_text()
                    .strip()
                )

        observation["controls"].append({

            "control_id":
                f"control_{control_number}",

            "role":
                "textbox",

            "label":
                label,

            "name":
                name,

            "element_id":
                element_id,

            "input_type":
                input_type,

            "placeholder":
                placeholder
        })

        control_number += 1

    # ==========================================
    # BUTTONS
    # ==========================================

    buttons = page.locator("button")

    for i in range(buttons.count()):

        element = buttons.nth(i)

        button_text = (
            element
            .inner_text()
            .strip()
        )

        observation["controls"].append({

            "control_id":
                f"control_{control_number}",

            "role":
                "button",

            "accessible_name":
                button_text,

            "button_type":
                element.get_attribute("type")
        })

        control_number += 1

    # ==========================================
    # TABLE DATA
    # ==========================================

    rows = page.locator("table tr")

    for i in range(rows.count()):

        row = rows.nth(i)

        cells = row.locator("td")

        # We only treat rows with exactly
        # two cells as label/value data.
        if cells.count() != 2:
            continue

        label = (
            cells.nth(0)
            .inner_text()
            .strip()
        )

        value = (
            cells.nth(1)
            .inner_text()
            .strip()
        )

        if not label or not value:
            continue

        observation["data"].append({

            "data_id":
                f"data_{data_number}",

            "label":
                label,

            "value":
                value,

            # Store the row position so we can
            # later construct a deterministic
            # locator for the value cell.
            "row_index":
                i
        })

        data_number += 1

    return observation