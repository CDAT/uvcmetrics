set(BASELINE_DIR "${metrics_SOURCE_DIR}/test/baselines")

  add_test("diags_test_01"
    "python"
${metrics_SOURCE_DIR}/test/diagtest01.py
${UVCMETRICS_TEST_DATA_DIRECTORY}
--baseline=${BASELINE_DIR}/ )

add_test("diags_test_02"
"python"
${metrics_SOURCE_DIR}/test/diagtest02.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}
--baseline=${BASELINE_DIR}/ )

#set_tests_properties(diags_test_02 PROPERTIES DEPENDS diags_test_01)

add_test("diags_test_03"
"python"
${metrics_SOURCE_DIR}/test/diagtest03.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}
--baseline=${BASELINE_DIR}/ )

#set_tests_properties(diags_test_03 PROPERTIES DEPENDS diags_test_02)

add_test("diags_test_04"
"python"
${metrics_SOURCE_DIR}/test/diagtest04.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )

#set_tests_properties(diags_test_04 PROPERTIES DEPENDS diags_test_03)

add_test("diags_test_4A"
"python"
${metrics_SOURCE_DIR}/test/diagtest4A.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )

#set_tests_properties(diags_test_4A PROPERTIES DEPENDS diags_test_04)

add_test("diags_test_05"
"python"
${metrics_SOURCE_DIR}/test/diagtest05.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )

#set_tests_properties(diags_test_05 PROPERTIES DEPENDS diags_test_4A)

add_test("diags_test_06"
"python"
${metrics_SOURCE_DIR}/test/diagtest06.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )

#set_tests_properties(diags_test_06 PROPERTIES DEPENDS diags_test_05)

add_test("diags_test_07"
"python"
${metrics_SOURCE_DIR}/test/diagtest07.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )

#set_tests_properties(diags_test_07 PROPERTIES DEPENDS diags_test_06)

add_test("diags_test_08"
"python"
${metrics_SOURCE_DIR}/test/diagtest08.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )

#set_tests_properties(diags_test_08 PROPERTIES DEPENDS diags_test_07)

add_test("diags_test_09"
"python"
${metrics_SOURCE_DIR}/test/diagtest09.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )

#set_tests_properties(diags_test_09 PROPERTIES DEPENDS diags_test_08)

add_test("diags_test_10"
"python"
${metrics_SOURCE_DIR}/test/diagtest10.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )

#set_tests_properties(diags_test_10 PROPERTIES DEPENDS diags_test_09)

add_test("diags_test_11"
"python"
${metrics_SOURCE_DIR}/test/diagtest11.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )

#set_tests_properties(diags_test_11 PROPERTIES DEPENDS diags_test_10)

add_test("diags_test_12"
"python"
${metrics_SOURCE_DIR}/test/diagtest12.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )

#set_tests_properties(diags_test_12 PROPERTIES DEPENDS diags_test_11)

add_test("diags_test_13"
"python"
${metrics_SOURCE_DIR}/test/diagtest13.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )

#set_tests_properties(diags_test_13 PROPERTIES DEPENDS diags_test_12)

add_test("diags_test_15"
"python"
${metrics_SOURCE_DIR}/test/diagtest15.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )
#set_tests_properties(diags_test_15 PROPERTIES DEPENDS diags_test_13)

add_test("diags_meta"
"python"
${metrics_SOURCE_DIR}/test/diagsmeta.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )
#set_tests_properties(diags_meta PROPERTIES DEPENDS diags_test_15)

add_test("diags_table_test"
"python"
${metrics_SOURCE_DIR}/test/tabletest.py
--datadir=${UVCMETRICS_TEST_DATA_DIRECTORY}/
--baseline=${BASELINE_DIR}/ )
#set_tests_properties(diags_table_test PROPERTIES DEPENDS diags_meta)
 