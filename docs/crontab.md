# Crontab jobs

```shell
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed
*/7  *  *  *  * /root/animaid/scripts/organize.sh
0  */2  *  *  * /root/animaid/scripts/update.sh

@reboot sleep 120 && /root/animaid/scripts/update.sh
```