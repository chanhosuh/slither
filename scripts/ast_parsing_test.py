import os
import subprocess
import json
import errno

from slither import Slither

result = subprocess.run(['solc', '--versions'], stdout=subprocess.PIPE)
solc_versions = result.stdout.decode("utf-8").split("\n")

# remove empty strings if any
solc_versions = [version for version in solc_versions if version != ""]
solc_versions.reverse()

print("using solc versions", solc_versions)

slither_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
test_dir = os.path.join(slither_root, "tests", "ast-parsing")

tests = {}

for name in os.listdir(test_dir):
    if not name.endswith(".sol"):
        continue

    test_name, test_ver = name[:-4].rsplit("-", 1)

    if test_name not in tests:
        tests[test_name] = []

    tests[test_name].append(test_ver)

# validate tests
for test, vers in tests.items():
    if len(vers) == 1:
        if vers[0] != "all":
            raise Exception("only one test found but not called all", test)
    else:
        for ver in vers:
            if ver not in solc_versions:
                raise Exception("base version not found", test, ver)

env = dict(os.environ)

failures = []

for test, vers in tests.items():
    print("running test", test)

    ver_idx = 0

    for ver in solc_versions:
        if ver_idx + 1 < len(vers) and vers[ver_idx + 1] == ver:
            ver_idx += 1

        test_file = os.path.join(test_dir, f"{test}-{vers[ver_idx]}.sol")
        print("testing", ver, test_file)

        try:
            env["SOLC_VERSION"] = ver
            os.environ.clear()
            os.environ.update(env)
            slither = Slither(test_file)

            actual = {}

            for contract in slither.contracts:
                actual[contract.name] = {}

                for callable in contract.functions + contract.modifiers:
                    actual[contract.name][callable.full_name] = callable.slithir_cfg_to_dot_str()

            expected_file = os.path.join(test_dir, "expected", f"{test}-{ver}.json")
            try:
                with open(expected_file, "r") as f:
                    expected = json.load(f)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

                with open(expected_file, "w") as f:
                    json.dump(actual, f, indent="  ")
                    expected = actual

            if json.dumps(expected) != json.dumps(actual):
                raise Exception("expected != actual", test_file, ver)
        except Exception as e:
            print("test failed", e)
            failures.append(e)

exit(-1 if len(failures) > 0 else 0)
