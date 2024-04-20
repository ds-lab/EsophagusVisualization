
class setText:

    @staticmethod
    def set_text(db_relation, description):

        if db_relation is not None:
            attributes = vars(db_relation)
            print(f" attributes: {attributes}")
            text = ""
            for attribute, value in attributes.items():
                if not (attribute == "_sa_instance_state" or attribute == "visit_id"):
                    text += f"{attribute}: {value}\n"
            return text
        else:
            return f"No {description} for the selected visit."


    @staticmethod
    def set_text_many(db_relations, description):

        if db_relations is not None:
            text = ""
            for db_relation in db_relations:
                attributes = vars(db_relation)
                for attribute, value in attributes.items():
                    if not (attribute == "_sa_instance_state" or attribute == "visit_id" or attribute == "botox_id" or
                            attribute == "medication_id"):
                        text += f"{attribute}: {value}\n"
                text += "-----\n"
            return text
        else:
            return f"No {description} for the selected visit.\n"
