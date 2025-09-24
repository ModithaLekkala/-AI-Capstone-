find . -type f -name '*.png' -print0 |
while IFS= read -r -d '' f; do
  base="${f%.png}"
  new="${base%_[0-9:.-]*}.png"
  if [[ "$f" != "$new" ]]; then
    mv -v -- "$f" "$new"
  fi
done

