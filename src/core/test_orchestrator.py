# Update these methods in test_orchestrator.py

async def test_single_library(
    self, 
    library_name: str,
    proxy_config: Dict[str, str],
    device: str = "iphone_x",
    use_browserforge: bool = False
) -> List[TestResult]:
    """
    Test a single library against all target URLs
    
    UPDATED: Now manages session for device consistency
    
    Args:
        library_name: Name of the library to test
        proxy_config: Proxy configuration dictionary
        device: Mobile device to emulate
        use_browserforge: Whether to use BrowserForge enhanced fingerprints
    
    Returns:
        List of TestResult objects (one per URL)
    """
    logger.info(f"Starting test for library: {library_name}")
    
    if use_browserforge:
        if self.browserforge_available:
            logger.info(f"🎭 BrowserForge mode ENABLED for {library_name}")
        else:
            logger.warning(f"⚠️ BrowserForge requested but not available, using standard mode")
            use_browserforge = False
    
    # Get library info (for logging/metadata)
    lib_info = self._get_library_info(library_name)
    if not lib_info:
        logger.warning(f"Library '{library_name}' not found in matrix, but will try to run anyway")
        category = "playwright"  # Default category
    else:
        category = lib_info.get("category", "playwright")
    
    # Get appropriate runner (enhanced or standard)
    runner = self._get_runner_for_library(library_name, use_browserforge=use_browserforge)
    if not runner:
        error_msg = f"No runner found for library: {library_name}"
        logger.error(error_msg)
        return [TestResult(
            library=library_name,
            category=category,
            test_name="runner_error",
            url="",
            success=False,
            error=error_msg,
            execution_time=0
        )]
    
    # START SESSION (NEW!) - Locks device for entire test run
    try:
        if hasattr(runner, 'start_session'):
            runner.start_session(device)
            logger.info(f"🔒 Device session started for {library_name}")
    except Exception as e:
        logger.warning(f"Could not start session: {e}")
    
    # Get mobile configuration
    mobile_configs = self.test_targets.get("mobile_configurations", {})
    mobile_config = mobile_configs.get(device, mobile_configs.get("iphone_x", {}))
    
    # Get wait configuration with reduced defaults
    wait_config = self.test_targets.get("wait_configuration", {})
    default_wait = wait_config.get("default_wait_time", 5)
    
    # Test against all target URLs
    test_targets = self.test_targets.get("test_targets", {})
    results = []
    
    for target_name, target_data in test_targets.items():
        url = target_data.get("url")
        # Use intelligent wait times based on page complexity
        if "creepjs" in target_name.lower() or "worker" in target_name.lower():
            wait_time = 8  # Worker pages need more time
        elif "fingerprint" in target_name.lower() or "bot" in target_name.lower():
            wait_time = 5  # Standard complex pages
        else:
            wait_time = 3  # Simple pages like IP check
        
        mode_indicator = "🎭" if use_browserforge else "📱"
        logger.info(f"{mode_indicator} Testing {library_name} on {target_name}: {url} (wait: {wait_time}s)")
        
        try:
            # Call runner's run_test method
            # NOTE: Runner will use SAME device for all tests due to session
            result = await runner.run_test(
                url=url,
                url_name=target_name,
                proxy_config=proxy_config,
                mobile_config=mobile_config,
                wait_time=wait_time
            )
            results.append(result)
            
        except Exception as e:
            logger.error(f"Test failed for {library_name} on {target_name}: {str(e)}")
            results.append(TestResult(
                library=library_name,
                category=category,
                test_name=target_name,
                url=url,
                success=False,
                error=str(e)[:200],
                execution_time=0
            ))
    
    # END SESSION (NEW!) - Clean up after all tests
    try:
        if hasattr(runner, 'end_session'):
            runner.end_session()
            logger.info(f"🔓 Device session ended for {library_name}")
    except Exception as e:
        logger.warning(f"Could not end session: {e}")
    
    # Verify device consistency
    devices_used = set()
    for result in results:
        if result.success and hasattr(result, 'additional_data') and isinstance(result.additional_data, dict):
            device_name = result.additional_data.get('device_name')
            if device_name:
                devices_used.add(device_name)
    
    if len(devices_used) > 1:
        logger.error(f"❌ CONSISTENCY ERROR: Multiple devices used: {devices_used}")
    elif len(devices_used) == 1:
        logger.info(f"✅ Device consistency verified: {devices_used.pop()}")
    
    return results
