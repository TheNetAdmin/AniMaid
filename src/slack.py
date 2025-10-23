import logging

from slack_webhook import Slack


class slack_client:
    def __init__(self, config, secret):
        self.logger = logging.getLogger("animaid.slack")
        self.url = secret["slack"]["webhook_url"]
        self.client = Slack(url=self.url)

    def notify_single(self, main_text):
        msg_block = [{"type": "section", "text": {"type": "mrkdwn", "text": main_text}}]
        msg_block.append({"type": "divider"})
        self.client.post(blocks=msg_block)

    def _notify_records(self, main_text, records=[]):
        if len(records) > 20:
            self.logger.warning(f"Too many records: {len(records)}, capping at 20")
            records = records[:20]

        msg_block = [
            {"type": "section", "text": {"type": "mrkdwn", "text": main_text}},
            {"type": "divider"},
        ]

        for r in records:
            blk = {"type": "section", "text": {"type": "mrkdwn", "text": r["title"]}}
            icon_found = False

            if "record" in r:
                dr = r["record"]
            else:
                dr = r

            for tag in dr.get("tags", []):
                if "bangumi" in tag and "icon" in tag["bangumi"]:
                    blk["accessory"] = {
                        "type": "image",
                        "image_url": "https://bangumi.moe/" + tag["bangumi"]["icon"],
                        "alt_text": tag["bangumi"]["name"],
                    }
                    icon_found = True
            if (
                not icon_found
                and "team" in dr.keys()
                and dr["team"]["icon"] is not None
            ):
                blk["accessory"] = {
                    "type": "image",
                    "image_url": "https://bangumi.moe/" + dr["team"]["icon"],
                    "alt_text": dr["team"]["name"],
                }

            msg_block.append(blk)

        msg_block.append({"type": "divider"})
        self.logger.debug(f"Posting to {self.url} -- {msg_block}")
        self.client.post(blocks=msg_block)

    def notify_new_records(self, records):
        self._notify_records("@channel Master~ 刚发现了这些新番，并加入下载列表了哟~", records)

    def notify_new_potential_records(self, records):
        self._notify_records("@channel Master~ 要不要考虑一下这些番剧？", records)

    def notify_organize(self):
        self.notify_single("@channel Master~ 已经帮您打扫完毕，所有文件已经整理并入库了哟~")

    def notify_exception(self, msg):
        self.notify_single(f"@channel Master! 有异常发生啦: \n{msg}")
