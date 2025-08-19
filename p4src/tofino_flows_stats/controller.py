print('\nE2E MIRROR CONFIGURATION')
bfrt.mirror.cfg.entry_with_normal(sid=1, direction='EGRESS', session_enable=True, ucast_egress_port=1, ucast_egress_port_valid=1).push()
print('→ mirror session set.\n')