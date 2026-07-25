# Tracer

{ source /home/ubuntu/.user_env && source /opt/.manus/webdev.sh.env && cd . && cd /home/ubuntu/guimitestai-docs; sudo pip3 install mkdocs-material 2>&1 | tail -3; echo ---; mkdocs build --strict 2>&1 | tail -20; }; __manus_ec=0; trap '' PIPE; printf %d:%sn 0 /home/ubuntu/guimitestai-docs 2>/dev/null >&3; trap - PIPE! info "Em breve"
    Esta seção está sendo preparada para a Sprint 2. Enquanto isso, consulte o [Quickstart](../getting-started/quickstart.md) para exemplos práticos.
