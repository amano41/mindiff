# mindiff

Calculate and display the delta of two sequences of lines (maybe read from files) with simplified diff format.
The output format is something like "diff with full context".
The entire contents of the second file are displayed alongside add, delete, or change markers.
This helps you to grasp the change from the old file to the new file, i.e., which lines of the first file have changed to become the second file.

```shell
$ cat file1.txt
apple
cherry
raspberry
orange
peach
lemon

$ cat file2.txt
apple
banana
cherry
strawberry
orange
lemon

$ mindiff file1.txt file2.txt
  apple
+ banana
  cherry
! strawberry
  orange
- peach
  lemon
```
