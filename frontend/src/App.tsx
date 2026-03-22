import { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./App.css";

interface VideoInfo {
  id?: string;
  title?: string;
  description?: string;
  thumbnail?: string;
  uploader?: string;
  duration?: number;
  formats?: Array<{
    format_id: string;
    ext: string;
    resolution: string;
    filesize: number;
    has_audio?: boolean;
  }>;
  error?: string;
  is_playlist?: boolean;
  video_count?: number;
  videos?: PlaylistVideo[];
}

interface PlaylistVideo {
  id: string;
  title: string;
  url: string;
  duration: number;
  thumbnail: string;
  uploader: string;
  uploader_id: string;
  index: number;
  selected: boolean;
}

interface Task {
  id: string;
  url: string;
  status: string;
  progress: ProgressData;
}

interface ProgressData {
  status: string;
  filename?: string;
  percent?: string;
  speed?: string;
  eta?: string;
  total_bytes?: number;
  downloaded_bytes?: number;
}

interface BatchTask {
  id: string;
  playlist_url: string;
  selected_indices: number[];
  format_id: string;
  audio_format?: string;
  status: string;
  progress: BatchProgressData;
  concurrency?: number;
  video_tasks?: Record<string, {
    task_id: string;
    status: string;
    title: string;
    index: number;
    progress?: TaskProgressData;
  }>;
}

interface BatchProgressData {
  status?: string;
  current_video_title?: string;
  current_video_index?: number;
  completed?: number;
  total?: number;
}

interface TaskProgressData {
  status: string;
  filename?: string;
  percent?: string;
  speed?: string;
  eta?: string;
  total_bytes?: number;
  downloaded_bytes?: number;
  total_bytes_str?: string;
  downloaded_bytes_str?: string;
}

// SVG Icons
const Icons = {
  Download: () => (
    <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
    </svg>
  ),
  Video: () => (
    <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 1.5v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M13.125 16.5h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 16.5c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5" />
    </svg>
  ),
  User: () => (
    <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
    </svg>
  ),
  Clock: () => (
    <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  CheckCircle: () => (
    <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  XCircle: () => (
    <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 15L12 12m0 0l3-3m-3 3l3 3m-3-3l-3 3M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  List: () => (
    <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" />
    </svg>
  ),
  Folder: () => (
    <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
    </svg>
  ),
  Settings: () => (
    <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  Search: () => (
    <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
    </svg>
  ),
  Info: () => (
    <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
    </svg>
  ),
  Check: () => (
    <svg className="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
    </svg>
  ),
  Cube: () => (
    <svg className="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
    </svg>
  ),
};

function App() {
  const [url, setUrl] = useState("");
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [batchTasks, setBatchTasks] = useState<BatchTask[]>([]);
  const [selectedFormat, setSelectedFormat] = useState("best");
  const [audioFormat, setAudioFormat] = useState("");
  const [downloadDir, setDownloadDir] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [tempDownloadDir, setTempDownloadDir] = useState("");
  const [selectedVideos, setSelectedVideos] = useState<Set<number>>(new Set());
  const [concurrency, setConcurrency] = useState(1);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    axios.get("/api/settings").then((res) => {
      setDownloadDir(res.data.download_dir);
    });

    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(
      `${wsProtocol}//${window.location.host}/ws/progress`,
    );
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "progress") {
        setTasks((prev) =>
          prev.map((t) =>
            t.id === data.task_id
              ? { ...t, progress: data.data, status: data.data.status }
              : t,
          ),
        );
      } else if (data.type === "batch_progress") {
        setBatchTasks((prev) =>
          prev.map((t) =>
            t.id === data.batch_id
              ? {
                  ...t,
                  progress: data.data,
                  status: data.data.status === 'batch_finished' ? 'completed' : 'downloading',
                  video_tasks: data.data.video_tasks || t.video_tasks,
                }
              : t,
          ),
        );
      }
    };
    wsRef.current = ws;

    const interval = setInterval(() => {
      axios.get("/api/tasks").then((res) => {
        setTasks(res.data);
      });
      axios.get("/api/batch-tasks").then((res) => {
        setBatchTasks(res.data);
      });
    }, 1000);

    return () => {
      ws.close();
      clearInterval(interval);
    };
  }, []);

  const handleParse = async () => {
    if (!url) return;
    setLoading(true);
    setVideoInfo(null);
    setSelectedVideos(new Set());
    try {
      const res = await axios.post("/api/parse", { url });
      setVideoInfo(res.data);

      if (res.data.is_playlist && res.data.videos) {
        const allIndices = new Set<number>(res.data.videos.map((v: PlaylistVideo) => v.index));
        setSelectedVideos(allIndices);
      } else if (res.data.formats?.length) {
        setSelectedFormat(res.data.formats[0].format_id);
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } } };
      setVideoInfo({ error: error.response?.data?.error || "解析失败" });
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!url) return;
    if (videoInfo?.is_playlist && selectedVideos.size > 0) {
      handleBatchDownload();
      return;
    }
    try {
      await axios.post("/api/download", {
        url,
        format_id: selectedFormat,
        audio_format: audioFormat || null,
      });
      setUrl("");
      setVideoInfo(null);
      setAudioFormat("");
    } catch (err) {
      console.error(err);
    }
  };

  const handleBatchDownload = async () => {
    if (!url || selectedVideos.size === 0) return;
    try {
      await axios.post("/api/download-batch", {
        playlist_url: url,
        selected_indices: Array.from(selectedVideos),
        format_id: selectedFormat,
        audio_format: audioFormat || null,
        concurrency: concurrency,
      });
      setUrl("");
      setVideoInfo(null);
      setSelectedVideos(new Set());
      setAudioFormat("");
    } catch (err) {
      console.error(err);
    }
  };

  const toggleVideoSelection = (index: number) => {
    setSelectedVideos((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const selectAllVideos = () => {
    if (videoInfo?.videos) {
      setSelectedVideos(new Set(videoInfo.videos.map((v) => v.index)));
    }
  };

  const deselectAllVideos = () => {
    setSelectedVideos(new Set());
  };

  const invertSelection = () => {
    if (videoInfo?.videos) {
      const allIndices = new Set(videoInfo.videos.map((v) => v.index));
      setSelectedVideos((prev) => {
        const newSet = new Set<number>();
        for (const idx of allIndices) {
          if (!prev.has(idx)) {
            newSet.add(idx);
          }
        }
        return newSet;
      });
    }
  };

  const openSettings = () => {
    setTempDownloadDir(downloadDir);
    setShowSettings(true);
  };

  const selectDirectory = async () => {
    try {
      const res = await axios.post("/api/settings/select-dir");
      if (res.data.status === "ok") {
        setTempDownloadDir(res.data.download_dir);
        setDownloadDir(res.data.download_dir);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const saveSettings = async () => {
    try {
      const res = await axios.post("/api/settings", {
        download_dir: tempDownloadDir,
      });
      setDownloadDir(res.data.download_dir);
      setShowSettings(false);
    } catch (err) {
      console.error(err);
    }
  };

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const formatSize = (bytes: number) => {
    if (!bytes) return "未知";
    const mb = bytes / 1024 / 1024;
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <Icons.Cube />
          <h1>VideoVault</h1>
        </div>
        <span className="version">v1.0.0</span>
      </header>

      <main className="main">
        <section className="input-section">
          <div className="input-card">
            <div className="url-input-wrapper">
              <div className="input-icon"><Icons.Search /></div>
              <input
                type="url"
                className="url-input"
                placeholder="粘贴 YouTube 视频或播放列表链接..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleParse()}
              />
              <button
                className="btn btn-primary"
                onClick={handleParse}
                disabled={loading || !url}
              >
                {loading ? "解析中..." : "获取信息"}
              </button>
            </div>
            <div className="input-hint">
              <div className="hint-icon"><Icons.Info /></div>
              <span>支持 YouTube 单个视频或播放列表，播放列表可批量选择下载</span>
            </div>
          </div>
        </section>

        {videoInfo && (
          <section className="video-info">
            {videoInfo.error ? (
              <div className="error-box">
                <Icons.XCircle />
                <span>{videoInfo.error}</span>
              </div>
            ) : videoInfo.is_playlist ? (
              <div className="playlist-card">
                <div className="playlist-header">
                  <div className="playlist-thumbnail">
                    {videoInfo.thumbnail && (
                      <img src={videoInfo.thumbnail} alt={videoInfo.title} />
                    )}
                  </div>
                  <div className="playlist-details">
                    <div className="detail-header">
                      <Icons.List />
                      <h2>{videoInfo.title}</h2>
                    </div>
                    <p className="uploader">
                      <Icons.User />
                      {videoInfo.uploader}
                    </p>
                    <p className="video-count">
                      共 <strong>{videoInfo.video_count}</strong> 个视频 · 已选择 <strong>{selectedVideos.size}</strong> 个
                    </p>

                    <div className="playlist-actions">
                      <button className="btn btn-secondary" onClick={selectAllVideos}>
                        全选
                      </button>
                      <button className="btn btn-secondary" onClick={deselectAllVideos}>
                        清空
                      </button>
                      <button className="btn btn-secondary" onClick={invertSelection}>
                        反选
                      </button>
                    </div>

                    <div className="format-select">
                      <label>视频格式</label>
                      <select
                        value={audioFormat ? "audio_only" : selectedFormat}
                        onChange={(e) => {
                          if (e.target.value === "audio_only") {
                            setAudioFormat("m4a");
                            setSelectedFormat("best");
                          } else {
                            setAudioFormat("");
                            setSelectedFormat(e.target.value);
                          }
                        }}
                      >
                        <optgroup label="视频">
                          <option value="best">最佳质量 (带音频)</option>
                          <option value="bestvideo+bestaudio">最佳视频+音频</option>
                        </optgroup>
                        <optgroup label="音频">
                          <option value="audio_only">仅提取音频</option>
                        </optgroup>
                      </select>
                    </div>

                    {audioFormat && (
                      <div className="format-select">
                        <label>音频格式</label>
                        <select
                          value={audioFormat}
                          onChange={(e) => setAudioFormat(e.target.value)}
                        >
                          <option value="m4a">M4A</option>
                          <option value="mp3">MP3</option>
                          <option value="wav">WAV</option>
                          <option value="aac">AAC</option>
                          <option value="flac">FLAC</option>
                          <option value="ogg">OGG</option>
                        </select>
                      </div>
                    )}

                    <div className="format-select">
                      <label>并发数量</label>
                      <select
                        value={concurrency}
                        onChange={(e) => setConcurrency(Number(e.target.value))}
                      >
                        <option value={1}>1 (推荐)</option>
                        <option value={2}>2</option>
                        <option value={3}>3</option>
                        <option value={5}>5</option>
                      </select>
                    </div>

                    <button
                      className="btn btn-success btn-large"
                      onClick={handleDownload}
                      disabled={selectedVideos.size === 0}
                    >
                      <Icons.Download />
                      下载选中的 {selectedVideos.size} 个视频
                    </button>
                  </div>
                </div>

                <div className="video-list">
                  {videoInfo.videos?.map((video) => (
                    <div
                      key={video.id}
                      className={`video-item ${selectedVideos.has(video.index) ? 'selected' : ''}`}
                      onClick={() => toggleVideoSelection(video.index)}
                    >
                      <div className="checkbox-wrapper">
                        <input
                          type="checkbox"
                          checked={selectedVideos.has(video.index)}
                          onChange={() => toggleVideoSelection(video.index)}
                          onClick={(e) => e.stopPropagation()}
                        />
                        <Icons.Check />
                      </div>
                      <div className="video-thumbnail">
                        {video.thumbnail && <img src={video.thumbnail} alt={video.title} />}
                      </div>
                      <div className="video-details">
                        <span className="video-index">{video.index}.</span>
                        <span className="video-title">{video.title}</span>
                        <span className="video-duration">
                          <Icons.Clock />
                          {formatDuration(video.duration)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="info-card">
                <div className="thumbnail">
                  {videoInfo.thumbnail && (
                    <img src={videoInfo.thumbnail} alt={videoInfo.title} />
                  )}
                </div>
                <div className="details">
                  <h2>{videoInfo.title}</h2>
                  <p className="uploader">
                    <Icons.User />
                    {videoInfo.uploader}
                  </p>
                  <p className="duration">
                    <Icons.Clock />
                    {formatDuration(videoInfo.duration || 0)}
                  </p>

                  <div className="format-select">
                    <label>视频格式</label>
                    <select
                      value={audioFormat ? "audio_only" : selectedFormat}
                      onChange={(e) => {
                        if (e.target.value === "audio_only") {
                          setAudioFormat("m4a");
                          setSelectedFormat("best");
                        } else {
                          setAudioFormat("");
                          setSelectedFormat(e.target.value);
                        }
                      }}
                    >
                      <optgroup label="视频">
                        <option value="best">最佳质量 (带音频)</option>
                        <option value="bestvideo+bestaudio">最佳视频+音频</option>
                        {videoInfo.formats
                          ?.filter(
                            (f) =>
                              f.resolution &&
                              !f.resolution.includes("audio only"),
                          )
                          .map((f) => (
                            <option key={f.format_id} value={f.format_id}>
                              {f.resolution} - {f.ext} ({formatSize(f.filesize)})
                            </option>
                          ))}
                      </optgroup>
                      <optgroup label="音频">
                        <option value="audio_only">仅提取音频</option>
                      </optgroup>
                    </select>
                  </div>

                  {audioFormat && (
                    <div className="format-select">
                      <label>音频格式</label>
                      <select
                        value={audioFormat}
                        onChange={(e) => setAudioFormat(e.target.value)}
                      >
                        <option value="m4a">M4A</option>
                        <option value="mp3">MP3</option>
                        <option value="wav">WAV</option>
                        <option value="aac">AAC</option>
                        <option value="flac">FLAC</option>
                        <option value="ogg">OGG</option>
                      </select>
                    </div>
                  )}

                  <button
                    className="btn btn-success btn-large"
                    onClick={handleDownload}
                  >
                    <Icons.Download />
                    开始下载
                  </button>
                </div>
              </div>
            )}
          </section>
        )}

        {batchTasks.length > 0 && (
          <section className="batch-progress-section">
            <h3>批量下载进度</h3>
            <div className="batch-task-list">
              {batchTasks.map((batch) => (
                <div key={batch.id} className="batch-task-item">
                  <div className="batch-header">
                    <span className="batch-url">{batch.playlist_url}</span>
                    <span className={`batch-status status-${batch.status}`}>
                      {batch.status === 'downloading' ? '下载中' :
                       batch.status === 'completed' ? '已完成' :
                       batch.status === 'partial_failed' ? '部分失败' :
                       batch.status === 'cancelled' ? '已取消' :
                       batch.status}
                    </span>
                  </div>

                  {batch.progress.total && (
                    <>
                      <div className="progress-bar">
                        <div
                          className="progress-fill"
                          style={{
                            width: `${((batch.progress.completed || 0) / batch.progress.total) * 100}%`
                          }}
                        />
                      </div>
                      <div className="batch-progress-info">
                        <span>{batch.progress.completed || 0} / {batch.progress.total} 个视频</span>
                        {batch.progress.current_video_title && (
                          <span className="current-video">
                            当前: {batch.progress.current_video_title}
                          </span>
                        )}
                      </div>
                    </>
                  )}

                  {batch.video_tasks && Object.keys(batch.video_tasks).length > 0 && (
                    <div className="video-tasks-progress">
                      <div className="video-tasks-header">视频详情</div>
                      {Object.entries(batch.video_tasks).map(([videoId, videoTask]) => (
                        <div key={videoId} className={`video-task-item status-${videoTask.status}`}>
                          <div className="video-task-info">
                            <span className="video-task-index">#{videoTask.index}</span>
                            <span className="video-task-title">{videoTask.title}</span>
                            <span className={`video-task-status status-${videoTask.status}`}>
                              {videoTask.status === 'downloading' ? '下载中' :
                               videoTask.status === 'completed' ? '已完成' :
                               videoTask.status === 'pending' ? '等待中' :
                               videoTask.status === 'failed' ? '失败' : videoTask.status}
                            </span>
                          </div>
                          {videoTask.progress && videoTask.progress.percent && videoTask.status === 'downloading' && (
                            <>
                              <div className="progress-bar">
                                <div
                                  className="progress-fill"
                                  style={{ width: videoTask.progress.percent }}
                                />
                              </div>
                              <div className="video-task-progress-info">
                                <span>{videoTask.progress.percent}</span>
                                {videoTask.progress.downloaded_bytes_str && videoTask.progress.total_bytes_str && (
                                  <span>• {videoTask.progress.downloaded_bytes_str} / {videoTask.progress.total_bytes_str}</span>
                                )}
                                {videoTask.progress.speed && (
                                  <span>• {videoTask.progress.speed}</span>
                                )}
                                {videoTask.progress.eta && (
                                  <span>• 剩余: {videoTask.progress.eta}</span>
                                )}
                              </div>
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="queue-section">
          <h3>下载队列</h3>
          {tasks.length === 0 ? (
            <p className="empty-queue">暂无下载任务</p>
          ) : (
            <div className="task-list">
              {tasks.map((task) => (
                <div key={task.id} className="task-item">
                  <div className="task-info">
                    <span className="task-url">{task.url}</span>
                    <span className={`task-status status-${task.status}`}>
                      {task.status === "downloading"
                        ? "下载中"
                        : task.status === "finished"
                          ? "完成"
                          : task.status === "pending"
                            ? "等待中"
                            : task.status === "error"
                              ? "错误"
                              : task.status}
                    </span>
                  </div>
                  {(task.progress as ProgressData)?.percent && (
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{
                          width:
                            (task.progress as ProgressData).percent || "0%",
                        }}
                      />
                    </div>
                  )}
                  {(task.progress as ProgressData)?.speed && (
                    <div className="progress-info">
                      {(task.progress as ProgressData).percent} •
                      {(task.progress as ProgressData).speed} • 剩余:{" "}
                      {(task.progress as ProgressData).eta}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </main>

      <footer className="footer">
        <div className="footer-dir">
          <Icons.Folder />
          <span>{downloadDir}</span>
        </div>
        <button className="btn-link" onClick={openSettings}>
          <Icons.Settings />
          设置
        </button>
      </footer>

      {showSettings && (
        <div className="modal-overlay" onClick={() => setShowSettings(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>设置</h3>
            <div className="setting-item">
              <label>下载目录</label>
              <div className="dir-input-group">
                <input
                  type="text"
                  value={tempDownloadDir}
                  onChange={(e) => setTempDownloadDir(e.target.value)}
                  placeholder="选择或输入目录路径"
                />
                <button className="btn" onClick={selectDirectory}>
                  浏览
                </button>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn" onClick={() => setShowSettings(false)}>
                取消
              </button>
              <button className="btn btn-primary" onClick={saveSettings}>
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
