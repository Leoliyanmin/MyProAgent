// Debug login - run this in browser console

async function debugLogin() {
  console.log('=== Starting Login Debug ===')
  
  try {
    // Test 1: Direct fetch to backend
    console.log('\n1. Testing direct backend connection...')
    const directResponse = await fetch('http://localhost:8001/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'admin@admin.com',
        password: '123456'
      })
    })
    const directResult = await directResponse.json()
    console.log('Direct backend response:', directResult)
    console.log('Has user?', !!directResult.user)
    
    // Test 2: Through Vite proxy
    console.log('\n2. Testing through Vite proxy...')
    const proxyResponse = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'admin@admin.com',
        password: '123456'
      })
    })
    console.log('Proxy response status:', proxyResponse.status)
    console.log('Proxy response ok?', proxyResponse.ok)
    
    const proxyResult = await proxyResponse.json()
    console.log('Proxy response data:', proxyResult)
    console.log('Has success?', 'success' in proxyResult)
    console.log('Has user?', !!proxyResult.user)
    console.log('User data:', proxyResult.user)
    
    // Test 3: Check what auth store receives
    console.log('\n3. Testing auth store...')
    const auth = window.__VUE__?.config?.globalProperties?.$pinia?.state?.value?.auth
    if (auth) {
      console.log('Auth store state:', {
        isAuthenticated: auth.isAuthenticated,
        user: auth.user,
        token: auth.token ? 'exists' : 'missing'
      })
    } else {
      console.log('Auth store not accessible from window')
    }
    
  } catch (err) {
    console.error('Debug error:', err)
  }
  
  console.log('\n=== Debug Complete ===')
}

// Run the debug
debugLogin()
