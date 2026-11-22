# fast/ — Astra の `kernel.c` と同じ呼び出し口のまま、分岐をなくした版（試作）

`kernel_fast.c` は、Astra の `libtri4.so` と同じ関数名・同じ引数で、内側のループを分岐のない形に書き直したものである。Astra の `cpython_fsum.c` と一緒にコンパイルし、`libtri4.so` を置き換えて使う。

```
gcc -std=c11 -O3 -mavx2 -ffp-contract=off -fno-fast-math -fno-trapping-math -fno-math-errno -fPIC -shared \
    -I<Python の include> kernel_fast.c <Astra の>/cpython_fsum.c -lm -o geoenclosereader/libtri4.so
```

結果は 133 件すべてで Python 版と一致したが、速さは Astra の版から 5〜10% しか変わらなかった。遅さの原因が算術ではないことを示す記録として残す。
