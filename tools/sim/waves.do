set WildcardFilter [lsearch -not -all -inline $WildcardFilter Memory]
log *
log -recursive /*
run -all
quit