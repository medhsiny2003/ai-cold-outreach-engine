def fix_indent():
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    inside_tab = False
    new_lines = []
    for line in lines:
        if line.startswith('with tab_copilot:'):
            inside_tab = True
            new_lines.append(line)
            continue
        elif line.startswith('# -------------------------------------------------------------\n') or line.startswith('# TAB 4: Revue & Édition'):
            if inside_tab and 'TAB 4' in line:
                inside_tab = False
        
        if inside_tab:
            # If line is not empty and doesn't already start with 4 spaces
            if line.strip() and not line.startswith('    '):
                new_lines.append('    ' + line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Indentation fixed successfully!")

if __name__ == '__main__':
    fix_indent()
