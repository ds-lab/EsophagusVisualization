
class setText:

    @staticmethod
    def set_text(db_relation, description):

        if db_relation is not None:
            attributes = vars(db_relation)
            text = ""
            first_attribute_skipped = False
            for attribute, value in attributes.items():
                if not first_attribute_skipped:
                    first_attribute_skipped = True
                    continue
                text += f"{attribute}: {value}\n"
            return text
        else:
            return f"No {description} for the selected visit."
