import { Select } from 'antd';
import { useMarketStore } from '../../store/marketSlice';

const options = [
  { value: 'ws', label: '实时 (WebSocket)' },
  { value: '5s', label: '5秒' },
  { value: '15s', label: '15秒' },
  { value: '30s', label: '30秒' },
  { value: '1min', label: '1分钟' },
  { value: 'manual', label: '手动刷新' },
];

export default function RefreshSelector() {
  const { refreshInterval, setRefreshInterval } = useMarketStore();

  return (
    <Select
      value={refreshInterval}
      onChange={setRefreshInterval}
      options={options}
      style={{ width: 180 }}
      size="small"
    />
  );
}
