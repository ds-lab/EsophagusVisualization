class setText:

    @staticmethod
    def set_text(db_relation, description):
        """
            This method is used to show the content of a DB-relation in a text-field as a list.
        """
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
        """
            This method is used to show the content of many DB-relation in a text-field as lists.
        """
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

    @staticmethod
    def set_text_two(db_relation1, description1, db_relation2, description2):
        """
            This method is used to show the content of two DB relations. The content of the first one is shown as a list
            (if not empty). For the second one it is only displayed if it exists in the DB or not.
            (This is for relations that can not be displayed as a list, e.g. xlsx-files).
        """
        text = ""
        if db_relation1 is not None:
            attributes = vars(db_relation1)
            print(f" attributes: {attributes}")
            for attribute, value in attributes.items():
                if not (attribute == "_sa_instance_state" or attribute == "visit_id"):
                    text += f"{attribute}: {value}\n"
        else:
            text += f"No {description1} for the selected visit.\n"
        if db_relation2 is not None:
            text += (f"------------------\n"
                     f"{description2} is/are in the Database.\n")
        else:
            text += (f"------------------\n"
                     f"No {description2} is/are in the Database.\n")
        return text
