from jx_base import DataClass


def diff_to_moves(unified_diff):
    """
    TODO: WE SHOULD BE ABLE TO STREAM THE RAW DIFF SO WE HANDLE LARGE ONES
    FOR EACH FILE, RETURN AN ARRAY OF (line, action) PAIRS
    :param unified_diff: raw diff
    :return: (file, line, action) triples
    """
    output = []
    files = FILE_SEP.split(unified_diff)[1:]
    for file_ in files:
        changes = []
        old_file_header, new_file_header, file_diff = file_.split("\n", 2)
        old_file_path = old_file_header[1:]  # eg old_file_header == "a/testing/marionette/harness/marionette_harness/tests/unit/unit-tests.ini"
        new_file_path = new_file_header[5:]  # eg new_file_header == "+++ b/tests/resources/example_file.py"

        c = 0, 0
        hunks = HUNK_SEP.split(file_diff)[1:]
        for hunk in hunks:
            line_diffs = hunk.split("\n")
            old_start, old_length, new_start, new_length = HUNK_HEADER.match(line_diffs[0]).groups()
            next_c = max(0, int(new_start)-1), max(0, int(old_start)-1)
            if next_c[0] - next_c[1] != c[0] - c[1]:
                Log.error("expecting a skew of {{skew}}", skew=next_c[0] - next_c[1])
            if c[0] > next_c[0]:
                Log.error("can not handle out-of-order diffs")
            while c[0] != next_c[0]:
                c = no_change(c)

            for line in line_diffs[1:]:
                if not line:
                    continue
                if (
                    line.startswith("new file mode") or
                    line.startswith("deleted file mode") or
                    line.startswith("index ") or
                    line.startswith("diff --git")
                ):
                    # HAPPENS AT THE TOP OF NEW FILES
                    # diff --git a/security/sandbox/linux/SandboxFilter.cpp b/security/sandbox/linux/SandboxFilter.cpp
                    # u'new file mode 100644'
                    # u'deleted file mode 100644'
                    # index a763e390731f5379ddf5fa77090550009a002d13..798826525491b3d762503a422b1481f140238d19
                    # GIT binary patch
                    # literal 30804
                    break
                d = line[0]
                if d != ' ':
                    changes.append(Action(line=int(c[0]), action=d))
                c = MOVE[d](c)

        output.append({
            "new": {"name": new_file_path},
            "old": {"name": old_file_path},
            "changes": changes
        })
    return wrap(output)


Action = DataClass(
    "Action",
    ["line", "action"],
    constraint=True  # TODO: remove when constrain=None is the same as True
)