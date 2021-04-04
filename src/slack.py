from slack_webhook import Slack


class slack_client:
    def __init__(self, config, secret):
        self.client = Slack(url=secret['slack']['webhook_url'])

    def notify_single(self, main_text):
        msg_block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": main_text
                }
            }
        ]
        msg_block.append({
            "type": "divider"
        })
        self.client.post(blocks=msg_block)

    def notify_records(self, main_text, records=[]):
        msg_block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": main_text
                }
            },
            {
                "type": "divider"
            }
        ]

        for r in records:
            blk = {
                "type": "section",
                "text": {
                        "type": "mrkdwn",
                        "text": r['title']
                }
            }
            if 'team' in r.keys() and r['team']['icon'] is not None:
                blk["accessory"] = {
                    "type": "image",
                    "image_url": 'https://bangumi.moe/' + r['team']['icon'],
                    "alt_text": r['team']['name']
                }
            msg_block.append(blk)

        msg_block.append({
            "type": "divider"
        })
        self.client.post(blocks=msg_block)

    def notify_new_records(self, records):
        self.notify_records('@channel Master~ 刚发现了这些新番，并加入下载列表了哟~', records)
    
    def notify_organize(self):
        self.notify_single('@channel Master~ 已经帮您打扫完毕，所有文件已经整理并入库了哟~')