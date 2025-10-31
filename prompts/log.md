# 1. Phân tích

### prompt:
```
Analyze this Project's features and identify all functions that need unit testing:

For each function, identify:
1. Main functionality
2. Input parameters and types
3. Expected return values
4. Potential edge cases
5. Dependencies that need mocking

Output into an md file `test/test_analystic.md`
```
OUTPUT: [test_analystic.md](test_analystic.md)

# 2. Thiết kế test case:

### prompt:
```
Generate comprehensive unit test cases for this Project's features based on this `test_analysis.md` document.
Output in a table with these columns `Category,Test Case, Input, Expected` and save into `test/test_design.md`
```
OUTPUT: [test_design.md](test_design.md)
 
# 3. Sinh Test Code
prompt: 

```
Based on this document `test/test_design.md`,
Create pytest unit tests for this Project's features.
Save all test in `test` folder
```

# 4. Chạy & Debug Tests
- Chạy lệnh: `run_test.sh`
=> lỗi: `ModuleNotFoundError: No module named 'pytests'`

prompt: 
```
Help me fix this error while run unit test:
`ModuleNotFoundError: No module named 'pytests'`
```

# 5. Tối ưu & Mocking
prompt:
```
Looking into `tests/*.py`, check if the test is optimized and show what to optimize if needed.
Then output to `prompts/optimize.md
```
OUTPUT: [optimize.md](optimize.md)

- Từ output trên, bắt đầu cho AI tối ưu.

prompt:
```
from this document, Optimize tests.
```
