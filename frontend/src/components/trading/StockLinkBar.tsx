import { Button, Space, Dropdown } from 'antd';
import { LinkOutlined, GlobalOutlined } from '@ant-design/icons';

interface Props {
  code: string;
}

export default function StockLinkBar({ code }: Props) {
  const isMobile = /Android|iPhone/i.test(navigator.userAgent);

  const links = {
    tonghuashun_web: `https://stockpage.10jqka.com.cn/${code}/`,
    eastmoney_web: `https://quote.eastmoney.com/${
      code.startsWith('6') ? 'sh' : 'sz'
    }${code}.html`,
    xueqiu: `https://xueqiu.com/S/${
      code.startsWith('6') ? 'SH' : 'SZ'
    }${code}`,
  };

  const webItems = [
    { key: 'eastmoney', label: '东方财富网页', onClick: () => window.open(links.eastmoney_web, '_blank') },
    { key: 'tonghuashun', label: '同花顺网页', onClick: () => window.open(links.tonghuashun_web, '_blank') },
    { key: 'xueqiu', label: '雪球网页', onClick: () => window.open(links.xueqiu, '_blank') },
  ];

  const appItems = [
    { key: 'ths_app', label: '同花顺App', onClick: () => { window.location.href = `ths://stock?code=${code}`; } },
    { key: 'xq_app', label: '雪球App', onClick: () => { window.location.href = `xueqiu://stock/${code.startsWith('6') ? 'SH' : 'SZ'}${code}`; } },
  ];

  return (
    <Space>
      <span style={{ fontSize: 12, color: '#999' }}>外部工具:</span>
      <Dropdown menu={{ items: webItems }}>
        <Button size="small" icon={<GlobalOutlined />}>
          网页版
        </Button>
      </Dropdown>
      {isMobile && (
        <Dropdown menu={{ items: appItems }}>
          <Button size="small" icon={<LinkOutlined />}>
            App版
          </Button>
        </Dropdown>
      )}
    </Space>
  );
}
