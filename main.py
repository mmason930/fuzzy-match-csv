from fuzzywuzzy import fuzz
import csv
import os
import sys
import re


def get_column_map(row):
    column_map = {}
    index = 0
    for col in row:
        column_map[str(col.strip())] = index
        index += 1
    return column_map


def clean_name(name):
    return re.sub(r'[^a-zA-Z0-9\s]', '', name)


def read_lookup_file():
    rows = []
    with open(lookup_file_path, "r", encoding='utf-8-sig') as lookup_file:
        lookup_reader = csv.reader(lookup_file, delimiter=',')
        lookup_column_map = get_column_map(next(lookup_reader))

        if lookup_column_map[lookup_upc_column_name] is None:
            print("The lookup file UPC column(" + lookup_upc_column_name + ") does not exist.")
            sys.exit(1)

        if lookup_column_map[lookup_product_name_column_name] is None:
            print("The lookup file product name column(" + lookup_product_name_column_name + ") does not exist.")
            sys.exit(1)

        for lookup_row in lookup_reader:
            lookup_name = lookup_row[lookup_column_map[lookup_product_name_column_name]]
            lookup_upc = lookup_row[lookup_column_map[lookup_upc_column_name]]

            rows.append({
                "upc": lookup_upc,
                "name": lookup_name,
                "name_clean": clean_name(lookup_name)
            })
    return rows


def find_best_match(source_product_name, lookup_rows):
    best_upc = ""
    best_name = ""
    best_ratio = 0

    for row in lookup_rows:
        lookup_name = row['name']
        lookup_name_clean = row['name_clean']
        lookup_upc = row['upc']
        current_row_ratio = fuzz.ratio(clean_name(source_product_name), lookup_name_clean)

        if current_row_ratio > best_ratio:
            best_ratio = current_row_ratio
            best_upc = lookup_upc
            best_name = lookup_name

    return {
        "upc": best_upc,
        "name": best_name,
        "score": best_ratio
    }


def input_or_default(prompt, default):
    value = input(prompt + "(default: " + default + "): ").strip()
    if len(value) == 0:
        return default
    return value


source_file_path = input_or_default("Enter the source file path", "source.csv")
lookup_file_path = input_or_default("Enter the lookup file path", "lookup.csv")
source_product_name_column_name = input_or_default("Enter the source file's product name column header", "product_name")
lookup_upc_column_name = input_or_default("Enter the lookup file's UPC column header", "upc")
lookup_product_name_column_name = input_or_default("Enter the lookup file's product name column header", "product_name")
output_file_path = input_or_default("Enter the output file path", "output.csv")


def main():

    if os.path.exists(source_file_path) is False:
        print("Source file does not exist: " + source_file_path)
        sys.exit(1)

    if os.path.exists(lookup_file_path) is False:
        print("Lookup file does not exist: " + lookup_file_path)
        sys.exit(1)

    lookup_rows = read_lookup_file()

    with open(source_file_path, "r", encoding='utf-8-sig') as source_file:
        with open(output_file_path, "w", encoding='utf-8-sig') as output_file:
            output_writer = csv.writer(output_file, delimiter=',')
            source_reader = csv.reader(source_file, delimiter=',')
            header_row = next(source_reader)
            source_column_map = get_column_map(header_row)
            counter = 0

            if source_column_map[source_product_name_column_name] is None:
                print("The source file product name column(" + source_product_name_column_name + ") does not exist.")
                sys.exit(1)

            # Write the header row to the output file
            output_header_row = header_row.copy()
            output_header_row.append("matching_upc")
            output_header_row.append("matching_name")
            output_header_row.append("matching_score")
            output_writer.writerow(output_header_row)

            for row in source_reader:

                counter += 1
                if counter % 100 == 0:
                    print("Processing line: " + str(counter))

                # Find the best match
                source_name = row[source_column_map[source_product_name_column_name]]
                best_match = find_best_match(source_name, lookup_rows)

                # Write the row to the results file
                write_row = row.copy()
                write_row.append(str(best_match["upc"]))
                write_row.append(str(best_match["name"]))
                write_row.append(str(best_match["score"]))
                output_writer.writerow(write_row)


if __name__ == '__main__':
    main()
